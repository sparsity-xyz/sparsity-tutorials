from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client

from autogen import LLMConfig
from autogen.agentchat import AssistantAgent
from autogen.mcp import create_toolkit
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

async def create_toolkit_and_run(session: ClientSession) -> None:
    # TODO: implement this
    pass


async def main():
    # TODO: implement this
    pass

if __name__ == "__main__":
    asyncio.run(main())
