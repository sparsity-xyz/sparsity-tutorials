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
    # Create a toolkit with available MCP tools
    toolkit = await create_toolkit(session=session)
    agent = AssistantAgent(name="assistant", llm_config=LLMConfig(model="gpt-4o-mini", api_type="openai",api_key=OPENAI_API_KEY))

    # Make a request using the MCP tool
    result = await agent.a_run(
        message="""1. Add 123223 and 456789
2.Get file content for 'ag2'
3.Get current date
4.Get price of AVAX""",
        tools=toolkit.tools,
        max_turns=2,
        user_input=False,
    )
    await result.process()
    print(await result.messages)


async def main():
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
        await create_toolkit_and_run(session)

if __name__ == "__main__":
    asyncio.run(main())
