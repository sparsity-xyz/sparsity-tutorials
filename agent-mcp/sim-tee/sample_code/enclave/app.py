import argparse
import dataclasses
import json
import os
import time

import requests
import uvicorn
from attestation import FixedKeyManager, MockFixedKeyManager
from autogen import LLMConfig
from autogen.agentchat import AssistantAgent
from autogen.mcp import create_toolkit
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel
from util.log import logger
from util.server import ENCLAVE_SERVER_PORT, Server

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

    def __init__(self, vsock: bool = False):
        self.vsock = vsock
        self.app = FastAPI()
        self.init_router()
        self.key = FixedKeyManager() if vsock else MockFixedKeyManager()

    def init_router(self):
        self.app.add_api_route("/ping", self.ping, methods=["GET"])
        self.app.add_api_route(
            "/attestation", self.attestation, methods=["GET"])
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
        toolkit = await create_toolkit(session=session)
        agent = AssistantAgent(name="assistant", llm_config=LLMConfig(
            model="gpt-4o-mini", api_type="openai", api_key=api_key))

        # Make a request using the MCP tool
        result = await agent.a_run(
            message=message,
            tools=toolkit.tools,
            max_turns=2,
            user_input=False,
        )
        await result.process()
        return result

    async def talk_to_ai(self, req: ChatRequest):
        nonce = bytes.fromhex(req.nonce)
        if len(nonce) < 8:
            return JSONResponse({"error": "invalid nonce, must be at least 8 characters long"})

        public_key = bytes.fromhex(req.public_key)
        data = bytes.fromhex(req.data)

        raw_data = self.key.decrypt(public_key, nonce, data)
        chat_data = ChatData(**json.loads(raw_data))
        if chat_data.api_key == "":
            return JSONResponse({"error": "empty api_key"})
        elif chat_data.ai_model == "":
            return JSONResponse({"error": "empty ai_model"})

        # Create server parameters for stdio connection
        server_params = StdioServerParameters(
            command="python",  # The command to run the server
            args=[
                str("mcp_server.py"),
                "stdio",
            ],  # Path to server script and transport mode
        )

        async with stdio_client(server_params) as (read, write), ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # set up tools and agent
            result = await self.create_toolkit_and_run(session, chat_data.api_key, chat_data.message)

        messages = await result.messages
        logger.info(messages)

        return self.response(messages)

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
    parser.add_argument("--vsock", action="store_true",
                        help="Enable vsock mode (optional)")
    args = parser.parse_args()

    app = APP(args.vsock)

    s = Server(ENCLAVE_SERVER_PORT, vsock=args.vsock)

    fd = s.fileno()
    uvicorn.run(app.app, fd=fd)
