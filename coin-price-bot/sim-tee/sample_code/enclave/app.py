import json
import argparse
import time
import dataclasses
import os

import requests
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from attestation import FixedKeyManager, MockFixedKeyManager
from util.server import Server, ENCLAVE_SERVER_PORT
from util.log import logger
from util.verifier import Verifier
from util.sign import Signer
from utils import url_prompt, extract_urls, custom_get, custom_post, fetch_html, summary_prompt, final_summary_prompt


HexStr = str


class ChatRequest(BaseModel):
    nonce: HexStr
    public_key: HexStr
    data: HexStr


@dataclasses.dataclass
class ChatData:
    api_key: str
    message: str
    platform: str = "openai"
    ai_model: str = "gpt-4"

    def json(self):
        return json.dumps(self, default=lambda o: o.__dict__)


class APP:
    app: FastAPI
    key: FixedKeyManager
    init: bool = False

    def __init__(self, vsock: bool=False):
        self.vsock = vsock
        self.app = FastAPI()
        self.init_router()
        self.key = FixedKeyManager() if vsock else MockFixedKeyManager()
        self.sparsity_endpoint = os.getenv("SPARSITY_ENDPOINT", "https://tee-app-2090887810.ap-northeast-2.elb.amazonaws.com")
        self.dest_tee_public_key = ""
        self.att: dict = {}
        self.signer = Signer()
        self.initialized = False


    def init_keys(self):
        if not self.verify_attestation():
            raise Exception('Attestation failed')
        self.dest_tee_public_key = self.att["public_key"].hex()
        logger.info(f"Dest TEE public key: {self.dest_tee_public_key}")
        self.initialized = True
    
    def verify_attestation(self) -> bool:
        logger.info("Verifying attestation: %s", self.sparsity_endpoint)

        try:
            att = custom_get(f"{self.sparsity_endpoint}/attestation")
            logger.info("Received attestation response")

            if att.get("mock"):
                self.att = {
                    "public_key": bytes.fromhex(att["attestation_doc"]["public_key"]),
                }
                logger.info("Attestation verification result: mock true")
                return True
            else:
                att = att["attestation_doc"]
                self.att = Verifier.decode_attestation_dict(att)
                result = Verifier.verify_attestation(att, "/app/util/root.pem")
                logger.info(f"Attestation verification result: {result}")
                return result
        except Exception as e:
            logger.error(f"Failed to verify attestation: {e}")
            return False

    def init_router(self):
        self.app.add_api_route("/ping", self.ping, methods=["GET"])
        self.app.add_api_route("/attestation", self.attestation, methods=["GET"])
        self.app.add_api_route("/query", self.test_query, methods=["GET"])
        self.app.add_api_route("/talk", self.talk_to_ai, methods=["POST"])
        self.app.add_api_route("/test-ping", self.test_query_tee, methods=["GET"])

    @staticmethod
    def ping(request: Request):
        return {"pong": int(time.time())}

    async def attestation(self, request: Request):
        if self.vsock:
            return JSONResponse({
                "attestation_doc": self.key.fixed_document
            })
        else:
            return JSONResponse({
                "attestation_doc": self.key.fixed_document,
                "mock": True
            })
    
    def verify_signature(self, data, sig):
        return Verifier.verify_signature(
            pub_key=bytes.fromhex(self.dest_tee_public_key),
            msg=data,
            signature=bytes.fromhex(sig)
        )

    async def talk_to_ai(self, req: ChatRequest):
        if not self.initialized:
            self.init_keys()

        req_resp_pairs = []

        nonce = bytes.fromhex(req.nonce)
        if len(nonce) < 8:
            return JSONResponse({"error": "invalid nonce, must be at least 8 characters long"})

        public_key = bytes.fromhex(req.public_key)
        data = bytes.fromhex(req.data)

        raw_data = self.key.decrypt(public_key, nonce, data)
        logger.info(f"Raw data: {raw_data}")

        chat_data = ChatData(**json.loads(raw_data))
        
        # Step 1: Modify user prompt to ask for relevant URLs
        original_message = chat_data.message
        url_list_prompt = url_prompt(chat_data.message)
        chat_data.message = url_list_prompt
        chat_data_encoded = chat_data.json().encode()

        # Send request to get URLs from sparsity endpoint
        url_res = self.send_verify_request(f"{self.sparsity_endpoint}/talk", chat_data_encoded)
        if url_res.get("error"):
            return JSONResponse({"got error from sparsity": url_res["error"]})
        req_resp_pairs.append(url_res)
        
        logger.info(f"URL response: {url_res}")
        url_response = url_res["data"]["response"]

        # Extract URLs from the response
        urls = extract_urls(url_response)
        logger.info(f"Extracted URLs: {urls}")

        # Step 2: Fetch HTML content for each URL
        url_html_dict = {}
        for url in urls[:3]:
            logger.info(f"Fetching HTML for: {url}")
            html = fetch_html(url)
            url_html_dict[url] = html

        # Step 3: Summarize each URL individually
        url_summary_dict = {}
        for url, html in url_html_dict.items():
            logger.info(f"Summarizing content for: {url}")
            sp = summary_prompt(original_message, url, html)
            temp_chat_data = ChatData(
                api_key=chat_data.api_key,
                message=sp,
                platform=chat_data.platform,
                ai_model=chat_data.ai_model
            )
            temp_chat_data_encoded = temp_chat_data.json().encode()
            summary_resp = self.send_verify_request(f"{self.sparsity_endpoint}/talk", temp_chat_data_encoded)
            logger.info(f"Summary response: {summary_resp}")
            url_summary_dict[url] = summary_resp["data"]["response"]
            logger.info(f"Summary for {url}: {url_summary_dict[url]}")
            req_resp_pairs.append(summary_resp)
        # Step 4: Prepare final summary request using individual summaries
        formatted_summaries = ""
        for i, (url, summary) in enumerate(url_summary_dict.items(), 1):
            formatted_summaries += f"url{i}:\n{url}\nSummary: {summary}\n\n"
        fsp = final_summary_prompt(original_message, formatted_summaries)
        chat_data.message = fsp
        chat_data_encoded = chat_data.json().encode()

        # Step 5: Send final summary request to sparsity endpoint
        final_resp = self.send_verify_request(f"{self.sparsity_endpoint}/talk", chat_data_encoded)
        if final_resp.get("error"):
            return JSONResponse({"got error from sparsity": final_resp["error"]})
        logger.info(f"Sparsity response data: {final_resp}")

        req_resp_pairs.append(final_resp)

        for i, pair in enumerate(req_resp_pairs):
            req_resp_pairs[i]["attestation_endpoint"] = f"{self.sparsity_endpoint}/attestation"
            if i == 0:
                req_resp_pairs[i]["description"] = "urls to resolve query"
            elif i == len(req_resp_pairs) - 1:
                req_resp_pairs[i]["description"] = "final summary combining all url content summaries"
            else:
                req_resp_pairs[i]["description"] = "summaries for the url content"

        return self.response(req_resp_pairs)

    async def test_query(self, request: Request):
        data = requests.get("https://api.binance.com/api/v3/time").json()
        return self.response(data)

    async def test_query_tee(self, request: Request):
        data = requests.get("https://tee-app-2090887810.ap-northeast-2.elb.amazonaws.com/ping", 
                            verify="/usr/local/share/ca-certificates/Certificate.crt").json()
        return self.response(data)

    def response(self, data):
        return JSONResponse({
            "sig": self.key.sign(data).hex(),
            "data": data,
        })
    
    def send_verify_request(self, url, data):
        # get pubkey and nonce to send to sparsity
        pubkey = self.signer.get_public_key_der().hex()
        nonce = os.urandom(8)

        spars_req = {
            "public_key": pubkey,
            "nonce": nonce.hex(),
            "data": self.signer.encrypt(bytes.fromhex(self.dest_tee_public_key), nonce, data).hex()
        }
        resp = custom_post(url, spars_req)
        if resp.get("error"):
            return JSONResponse({"got error from sparsity": resp["error"]})
        
        sig_valid = self.verify_signature(resp['data'], resp['sig'])
        if not sig_valid:
            return JSONResponse({"error": "invalid signature from the sparsity endpoint"})
        
        return resp


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--vsock", action="store_true", help="Enable vsock mode (optional)")
    args = parser.parse_args()

    app = APP(args.vsock)

    s = Server(ENCLAVE_SERVER_PORT, vsock=args.vsock)

    fd = s.fileno()
    uvicorn.run(app.app, fd=fd)
