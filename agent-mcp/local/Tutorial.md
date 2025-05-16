# Building an AutoGen Agent with MCP Integration

This tutorial walks through creating an AutoGen agent that communicates with an MCP server to perform various tasks. We'll build two main components:
1. An agent file (`ag2_agent.py`) that creates and runs the AutoGen assistant
2. An MCP server file (`mcp_server.py`) that provides tools for the agent to use

## 1. Setting Up Dependencies

First, let's create a `requirements.txt` file with all necessary dependencies:

```
mcp==1.8.1
python-dotenv==1.0.1
openai==1.78.1
asyncio==3.4.3
google-genai==1.15.0
vertexai==1.71.1
ag2==0.9.1.post0
python-binance==1.0.28
```

Install these dependencies:

```bash
pip install -r requirements.txt
```

## 2. Setting Up Environment Variables

Create a `.env` file in your project directory to store API keys:

```
OPENAI_API_KEY=your_openai_api_key_here
```

The OpenAI key will be used by the AutoGen agent to access language models.

## 3. Creating the Agent File (ag2_agent.py)

Let's build our agent file step by step:

### Import Necessary Modules

```python
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from autogen import LLMConfig
from autogen.agentchat import AssistantAgent
from autogen.mcp import create_toolkit
import asyncio
from dotenv import load_dotenv
import os
```

### Load Environment Variables

```python
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
```

### Define the create_toolkit_and_run Function

This function creates an AutoGen assistant with MCP tools and runs it:

```python
async def create_toolkit_and_run(session: ClientSession) -> None:
    # Create a toolkit with available MCP tools
    toolkit = await create_toolkit(session=session)
    agent = AssistantAgent(
        name="assistant", 
        llm_config=LLMConfig(
            model="gpt-4o-mini", 
            api_type="openai",
            api_key=OPENAI_API_KEY
        )
    )

    # Make a request using the MCP tool
    result = await agent.a_run(
        message="""1. Add 123223 and 456789
2. Get file content for 'ag2'
3. Get current date
4. Get price of AVAX""",
        tools=toolkit.tools,
        max_turns=2,
        user_input=False,
    )
    await result.process()
    print(await result.messages)
```

### Define the Main Function

The main function establishes a connection with the MCP server:

```python
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
```

## 4. Creating the MCP Server (mcp_server.py)

Now let's create the MCP server that provides tools for our agent:

```python
import argparse
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from binance.client import Client

mcp = FastMCP("McpServer")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b

@mcp.tool()
def get_current_date() -> str:
    """Get the current date"""
    return datetime.now().strftime("%Y-%m-%d")

@mcp.tool()
def get_coin_price(symbol: str) -> float:
    """Get the price of a coin by ticker symbol. Default denominator is USDT."""
    client = Client()
    symbol_usdt = symbol + "USDT"
    price = client.get_symbol_ticker(symbol=symbol_usdt)
    return float(price["price"])

# Creating a simple key-value store for files
files = {
    "ag2": "AG has released 0.8.5 version on 2025-04-03",
}

@mcp.resource("server-file://{name}")
def get_server_file(name: str) -> str:
    """Get a file content"""
    return files.get(name, f"File not found: {name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP Server")
    parser.add_argument("transport", choices=["stdio", "sse"], help="Transport mode (stdio or sse)")
    args = parser.parse_args()

    mcp.run(transport=args.transport)
```

## 5. Running the System

To run the system:

1. Make sure both files are in the same directory
2. Run the agent:

```bash
python ag2_agent.py
```

The agent will:
1. Start the MCP server in a subprocess
2. Create an AutoGen assistant with MCP tools
3. Run the assistant with the provided prompt
4. Display the assistant's messages

## 6. Extending Functionality

You can extend the MCP server by adding more tools. Here are some examples:

### String Operations Tool

```python
@mcp.tool()
def reverse_string(text: str) -> str:
    """Reverse a string"""
    return text[::-1]

@mcp.tool()
def count_words(text: str) -> int:
    """Count words in a string"""
    return len(text.split())
```

### File Operations Tool

```python
@mcp.tool()
def read_text_file(filename: str) -> str:
    """Read content of a text file"""
    try:
        with open(filename, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error: {str(e)}"
```

### Math Operations Tool

```python
@mcp.tool()
def square_root(number: float) -> float:
    """Calculate square root of a number"""
    import math
    return math.sqrt(number)
```

By adding these and other simple tools, you can enhance the capabilities of your AutoGen-MCP integration to perform a wide range of tasks.