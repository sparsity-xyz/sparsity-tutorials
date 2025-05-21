# Building an AutoGen Agent with MCP Integration

This tutorial walks through creating an AutoGen agent that communicates with an MCP server to perform various tasks. We'll build two main components:
1. An agent file (`ag2_agent.py`) that creates and runs the AutoGen assistant
2. An MCP server file (`mcp_server.py`) that provides tools for the agent to use

## Working Directory

**Important:** For this tutorial, all files (`requirements.txt`, `.env`, `ag2_agent.py`, `mcp_server.py`) should be created and run from within the `agent-mcp/local/workspace` directory.

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

Create a `.env` file in your `agent-mcp/local/workspace` directory to store API keys:

```
OPENAI_API_KEY=your_openai_api_key_here
# GEMINI_API_KEY=your_gemini_api_key_here # If you plan to use Gemini models
```

The OpenAI key will be used by the AutoGen agent to access language models.

## 3. Creating the Agent File (`ag2_agent.py`)

Your `ag2_agent.py` file in the `workspace` directory will define how the AutoGen agent connects to the MCP server and what tasks it performs. You'll need to fill in some parts.

### Import Necessary Modules

Ensure these imports are at the top of your `ag2_agent.py`:

```python
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client # Make sure this matches your intended client type
from autogen import LLMConfig
from autogen.agentchat import AssistantAgent
from autogen.mcp import create_toolkit
import asyncio
from dotenv import load_dotenv
import os
```

### Load Environment Variables

Next, load your API keys:

```python
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # Uncomment if using Gemini
```

### Define the `create_toolkit_and_run` Function

This asynchronous function is responsible for setting up the AutoGen assistant, providing it with tools from the MCP session, and then running it with a specific task. Your `ag2_agent.py` currently has this as a skeleton (`# TODO: implement this`).

Replace the `pass` statement with the following implementation:

```python
async def create_toolkit_and_run(session: ClientSession) -> None:
    # Create a toolkit with available MCP tools from the session
    toolkit = await create_toolkit(session=session)
    
    # Configure the LLM for the AssistantAgent
    # Ensure OPENAI_API_KEY is loaded correctly
    agent = AssistantAgent(
        name="assistant", 
        llm_config=LLMConfig(
            model="gpt-4o-mini", 
            api_type="openai",
            api_key=OPENAI_API_KEY # Make sure this variable holds your key
        )
    )

    # Define the message/task for the agent
    # This example asks the agent to use multiple tools provided by mcp_server.py
    message_to_agent = """1. Add 123223 and 456789
2. Get file content for 'ag2'
3. Get current date
4. Get price of AVAX"""

    # Make the request to the agent using the MCP tools
    result = await agent.a_run(
        message=message_to_agent,
        tools=toolkit.tools,      # Tools obtained from the MCP session
        max_turns=2,              # Limit the number of conversational turns
        user_input=False,         # Agent should not ask for user input during this run
    )
    
    # Process and print the results
    await result.process() # Ensure any post-processing or finalization of results occurs
    print("Agent run complete. Messages:")
    print(await result.messages) # Print the conversation history or final messages
```
**Explanation:**
- `create_toolkit(session=session)`: This function, provided by `autogen.mcp`, inspects the MCP `session` and makes the tools advertised by the server available to the AutoGen agent.
- `AssistantAgent(...)`: We initialize a standard AutoGen `AssistantAgent`. The `llm_config` is crucial for defining which LLM to use (here, OpenAI's `gpt-4o-mini`) and providing the necessary API key.
- `agent.a_run(...)`: This executes the agent. 
    - `message`: The prompt or task for the agent.
    - `tools=toolkit.tools`: This passes the MCP tools to the agent.
    - `max_turns` and `user_input` control the agent's execution behavior.
- `result.process()` and `result.messages`: These handle the output from the agent run.

### Define the Main Asynchronous Function (`main`)

The `main` function sets up and manages the connection to the MCP server. Your `ag2_agent.py` also has this as a skeleton (`# TODO: implement this`).

Replace the `pass` statement with the following implementation:

```python
async def main():
    # Define parameters for connecting to the MCP server via stdio
    # This tells the client how to start and communicate with mcp_server.py
    server_params = StdioServerParameters(
        command="python",  # Command to execute the server script
        args=[
            str("mcp_server.py"), # The MCP server script
            "stdio",                # The transport mode for communication
        ],
    )

    # Establish a client session with the MCP server
    # stdio_client handles starting the server subprocess and setting up communication pipes
    async with stdio_client(server_params) as (read, write), ClientSession(read, write) as session:
        # Initialize the MCP session (e.g., handshake, discover tools)
        await session.initialize()
        
        # Run the agent logic using the established session
        await create_toolkit_and_run(session)

if __name__ == "__main__":
    asyncio.run(main()) # Run the main asynchronous function
```
**Explanation:**
- `StdioServerParameters`: This configures how the `stdio_client` will launch your `mcp_server.py`. It specifies the command (`python`), the script name, and the argument `stdio` (which `mcp_server.py` expects to select its transport mode).
- `stdio_client(server_params)`: This context manager starts the `mcp_server.py` subprocess and provides `read` and `write` streams for communication.
- `ClientSession(read, write)`: This context manager uses the streams to establish an MCP session.
- `session.initialize()`: Performs any necessary setup for the MCP session, like discovering the tools available on the server.
- `create_toolkit_and_run(session)`: Calls the function we defined earlier, passing the active MCP session.

## 4. Creating the MCP Server (`mcp_server.py`)

Your `mcp_server.py` in the `workspace` directory provides tools that the AutoGen agent can use. Some of these tools are currently skeletons.

### Basic Structure and Imports
Ensure your server file starts like this:
```python
import argparse
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from binance.client import Client # For the get_coin_price tool

mcp = FastMCP("McpServer") # Initialize the MCP server instance
```

### Implementing the Tools

#### `add` tool
Your `mcp_server.py` has:
```python
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    # TODO: implement this
    pass
```
Replace `pass` with the correct implementation:
```python
    return a + b
```

#### `multiply` tool
Your `mcp_server.py` has:
```python
@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    # TODO: implement this
    pass
```
Replace `pass` with:
```python
    return a * b
```

#### `get_current_date` tool
Your `mcp_server.py` has:
```python
@mcp.tool()
def get_current_date() -> str:
    """Get the current date"""
    # TODO: implement this
    pass
```
Replace `pass` with:
```python
    return datetime.now().strftime("%Y-%m-%d")
```

### Existing Tools (Review)
Your `mcp_server.py` should already have the following tools implemented. Review them to understand how they work:

**`get_coin_price` tool:**
```python
@mcp.tool()
def get_coin_price(symbol: str) -> float:
    """Get the price of a coin by ticker symbol. Default denominator is USDT."""
    client = Client() # Note: API keys for Binance might be needed for extensive use or different endpoints
    symbol_usdt = symbol.upper() + "USDT"
    price = client.get_symbol_ticker(symbol=symbol_usdt)
    return float(price["price"])
```

**File Resource (`get_server_file`):**
This uses a simple dictionary as a stand-in for a file system.
```python
files = {
    "ag2": "AG has released 0.8.5 version on 2025-04-03",
}

@mcp.resource("server-file://{name}")
def get_server_file(name: str) -> str:
    """Get a file content"""
    return files.get(name, f"File not found: {name}")
```

### Server Execution Block
Ensure the server can be run with a transport mode argument:
```python
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP Server")
    parser.add_argument("transport", choices=["stdio", "sse"], help="Transport mode (stdio or sse)")
    args = parser.parse_args()

    mcp.run(transport=args.transport)
```
This part allows `ag2_agent.py` to start `mcp_server.py` in `stdio` mode.

## 5. Running the System

To run the system (once you have filled in the TODOs):

1. Make sure both `ag2_agent.py` and `mcp_server.py` are in your `agent-mcp/local/workspace` directory.
2. Ensure your `.env` file with the `OPENAI_API_KEY` is also in this directory.
3. Run the agent from the `agent-mcp/local/workspace` directory:

```bash
python ag2_agent.py
```

The agent (`ag2_agent.py`) will:
1. Start the MCP server (`mcp_server.py`) as a subprocess using stdio communication.
2. Initialize an MCP session with the server.
3. Create an AutoGen assistant, providing it with the tools discovered from the MCP server.
4. Run the assistant with the multi-step prompt defined in `create_toolkit_and_run`.
5. The assistant will use the MCP tools (like `add`, `get_server_file`, `get_current_date`, `get_coin_price`) by making calls back to the `mcp_server.py` process.
6. Finally, the agent will print the conversation messages, showing the results of the tool calls.

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