import os
import json
import argparse
import time
import dataclasses

import requests
import uvicorn

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from autogen import LLMConfig
from autogen.agentchat import AssistantAgent
from autogen.mcp import create_toolkit

from attestation import FixedKeyManager, MockFixedKeyManager
from util.server import Server, ENCLAVE_SERVER_PORT
from util.log import logger


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
    
    async def create_toolkit_and_run(self, session: ClientSession, api_key: str, message: str):
        # TODO: Implement the toolkit creation and agent execution
        #
        # Hint 1: Use create_toolkit() to create a toolkit using the provided session
        # Hint 2: Create an AssistantAgent with appropriate LLMConfig (model, api_type, api_key)
        # Hint 3: Run the agent with the user's message and the toolkit's tools
        # Hint 4: Process the result and return it
        #
        # The function should:
        # 1. Create a toolkit using the session
        # 2. Initialize an AI assistant agent with the provided API key
        # 3. Run the agent with the user's message and toolkit
        # 4. Process and return the result

        pass

    async def talk_to_ai(self, req: ChatRequest):
        # TODO: Implement the endpoint that processes encrypted chat requests
        #
        # Hint 1: Validate the nonce and extract the public_key and encrypted data
        # Hint 2: Decrypt the data using the key manager (self.key.decrypt)
        # Hint 3: Parse the decrypted data into a ChatData object
        # Hint 4: Validate that the API key and model are provided
        # Hint 5: Set up the stdio connection with proper parameters
        # Hint 6: Create a session, initialize it, and run the toolkit
        # Hint 7: Get the messages from the result and return a signed response
        #
        # The function should:
        # 1. Extract and validate request parameters (nonce, public_key, data)
        # 2. Decrypt the data and convert to ChatData
        # 3. Validate required fields
        # 4. Set up a stdio connection and create a client session
        # 5. Initialize the session and create/run the toolkit
        # 6. Get the messages from the result
        # 7. Return a signed response using self.response()
        
        # Begin with input validation
        nonce = bytes.fromhex(req.nonce)
        if len(nonce) < 8:
            return JSONResponse({"error": "invalid nonce, must be at least 8 characters long"})

        # Extract the public key and encrypted data
        public_key = bytes.fromhex(req.public_key)
        data = bytes.fromhex(req.data)

        # Continue implementation from here...
        pass

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
