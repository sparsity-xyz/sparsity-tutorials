import json
import argparse
import time
import dataclasses

import requests
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from attestation import FixedKeyManager, MockFixedKeyManager
from ai_models.open_ai import OpenAI, Platform
from ai_models.anthropic import Anthropic
from ai_models.gemini import Gemini
from util.server import Server, ENCLAVE_SERVER_PORT


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


class APP:
    app: FastAPI
    key: FixedKeyManager
    init: bool = False

    def __init__(self, vsock: bool=False):
        self.vsock = vsock
        self.app = FastAPI()
        self.init_router()
        self.key = FixedKeyManager() if vsock else MockFixedKeyManager()
        self.platform_mapping: dict[str: Platform] = {
            "openai": OpenAI,
            "anthropic": Anthropic,
            "gemini": Gemini,
        }

    def init_router(self):
        self.app.add_api_route("/ping", self.ping, methods=["GET"])
        self.app.add_api_route("/attestation", self.attestation, methods=["GET"])
        self.app.add_api_route("/query", self.test_query, methods=["GET"])
        self.app.add_api_route("/talk", self.talk_to_ai, methods=["POST"])

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

    async def talk_to_ai(self, req: ChatRequest):
        nonce = bytes.fromhex(req.nonce)
        if len(nonce) < 8:
            return JSONResponse({"error": "invalid nonce, must be at least 8 characters long"})

        public_key = bytes.fromhex(req.public_key)
        data = bytes.fromhex(req.data)

        raw_data = self.key.decrypt(public_key, nonce, data)
        chat_data = ChatData(**json.loads(raw_data))
        if chat_data.api_key == "":
            return JSONResponse({"error": "invalid api_key"})
        if self.platform_mapping.get(chat_data.platform) is None:
            return JSONResponse({"error": "invalid platform"})

        client: Platform = self.platform_mapping[chat_data.platform](chat_data.api_key)
        if not client.check_support_model(chat_data.ai_model):
            return JSONResponse({"error": "invalid ai model"})

        resp_content, resp_timestamp = client.call(chat_data.ai_model, chat_data.message)

        data = {
            "platform": chat_data.platform,
            "ai_model": chat_data.ai_model,
            "timestamp": resp_timestamp,
            "message": chat_data.message,
            "response": resp_content
        }
        return self.response(data)

    async def test_query(self, request: Request):
        data = requests.get("https://api.binance.com/api/v3/time").json()
        return self.response(data)

    def response(self, data):
        return JSONResponse({
            "sig": self.key.sign(data).hex(),
            "data": data,
        })


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--vsock", action="store_true", help="Enable vsock mode (optional)")
    args = parser.parse_args()

    app = APP(args.vsock)

    s = Server(ENCLAVE_SERVER_PORT, vsock=args.vsock)

    fd = s.fileno()
    uvicorn.run(app.app, fd=fd)
