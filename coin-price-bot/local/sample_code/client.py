import json
import os
import re

import requests
from util.signer import Signer
from util.verifier import Verifier


class ClientRequest:
    tee_endpoint: str
    public_key: str = ""
    api_key: str
    att: dict

    def __init__(self, tee_endpoint: str = "http://127.0.0.1:8000"):
        self.api_key = os.getenv("PLATFORM_API_KEY")
        self.platform = os.getenv("PLATFORM")
        self.model = os.getenv("MODEL")
        if not self.api_key:
            raise Exception('API key is required')
        self.tee_endpoint = tee_endpoint
        self.signer = Signer()
        self.init_keys()

    def init_keys(self):
        if not self.verify_attestation():
            raise Exception('Attestation failed')
        self.public_key = self.att["public_key"].hex()

    def verify_attestation(self) -> bool:
        att = requests.get(f"{self.tee_endpoint}/attestation").json()
        if att.get("mock"):
            self.att = {
                "public_key": bytes.fromhex(att["attestation_doc"]["public_key"]),
            }
            print("attestation verification result: mock true")
            return True
        else:
            att = att["attestation_doc"]
            self.att = Verifier.decode_attestation_dict(att)
            result = Verifier.verify_attestation(att, "./util/root.pem")
            print("Verifying TEE Enclave Identity:", result)
            return result

    def extract_urls(self, text):
        # Simple regex for URLs (can be improved)
        url_pattern = r'https?://[^\s,]+'
        return re.findall(url_pattern, text)

    def fetch_url_content(self, url):
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            return ""

    def chat(self, message: str):
        # 1. Ask TEE for URLs that can answer the user's prompt
        url_prompt = (
            f"List 5 exact URLs (no explanations, just the URLs, one per line) "
            f"that would help answer the following question:\n\n{message}\n"
        )
        data = {
            "api_key": self.api_key,
            "message": url_prompt,
            "platform": self.platform,
            "ai_model": self.model,
        }
        nonce = os.urandom(32)
        req = {
            "nonce": nonce.hex(),
            "public_key": self.signer.get_public_key_der().hex(),
            "data": self.signer.encrypt(bytes.fromhex(self.public_key), nonce, json.dumps(data).encode()).hex()
        }
        url_resp = requests.post(f"{self.tee_endpoint}/talk", json=req).json()
        print("\nStep 1: URL response:", url_resp)
        url_text = url_resp["data"]["response"]
        urls = self.extract_urls(url_text)
        print("Extracted URLs:", urls)

        # 2. Fetch content for each URL
        url_contents = {}
        for url in urls:
            print(f"\nFetching content for: {url}")
            url_contents[url] = self.fetch_url_content(url)

        # 3. Summarize each URL's content via TEE
        summaries = {}
        for url, content in url_contents.items():
            if not content.strip():
                summaries[url] = "[No content fetched]"
                continue
            summary_prompt = (
                f"Given the original question:\n{message}\n\n"
                f"Summarize the following content from {url} in a way that is relevant to the question:\n\n{content[:10000]}"
            )
            data = {
                "api_key": self.api_key,
                "message": summary_prompt,
                "platform": self.platform,
                "ai_model": self.model,
            }
            nonce = os.urandom(32)
            req = {
                "nonce": nonce.hex(),
                "public_key": self.signer.get_public_key_der().hex(),
                "data": self.signer.encrypt(bytes.fromhex(self.public_key), nonce, json.dumps(data).encode()).hex()
            }
            summary_resp = requests.post(
                f"{self.tee_endpoint}/talk", json=req).json()
            print(f"\nSummary for {url}:", summary_resp)
            summaries[url] = summary_resp["data"]["response"]

        # 4. Final summary: ask TEE to synthesize all summaries into a final answer
        combined_summaries = "\n\n".join(
            f"URL: {url}\nSummary: {summary}" for url, summary in summaries.items()
        )
        final_prompt = (
            f"Given the original question:\n{message}\n\n"
            f"and the following summaries from various sources:\n\n{combined_summaries}\n\n"
            f"Provide a concise, well-sourced answer to the original question."
        )
        data = {
            "api_key": self.api_key,
            "message": final_prompt,
            "platform": self.platform,
            "ai_model": self.model,
        }
        nonce = os.urandom(32)
        req = {
            "nonce": nonce.hex(),
            "public_key": self.signer.get_public_key_der().hex(),
            "data": self.signer.encrypt(bytes.fromhex(self.public_key), nonce, json.dumps(data).encode()).hex()
        }
        final_resp = requests.post(
            f"{self.tee_endpoint}/talk", json=req).json()
        print("\nFinal synthesized answer:", final_resp["data"]["response"])
        print("verify signature:", self.verify_sig(
            final_resp["data"], final_resp["sig"]))

        return final_resp["data"]["response"]

    def verify_sig(self, data, sig) -> bool:
        return Verifier.verify_signature(
            pub_key=bytes.fromhex(self.public_key),
            msg=data,
            signature=bytes.fromhex(sig),
        )
