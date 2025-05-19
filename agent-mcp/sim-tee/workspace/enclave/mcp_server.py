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
    from datetime import datetime
    try:
        result = datetime.now().strftime("%Y-%m-%d")
        print(f"[DEBUG] get_current_date result: {result}")
        return result
    except Exception as e:
        print(f"[ERROR] get_current_date failed: {e}")
        return f"Error: {e}"

@mcp.tool()
def get_coin_price(symbol: str) -> float:
    """Get the price of a coin by ticker symbol. Default denominator is USDT."""
    client = Client()
    symbol_usdt = symbol + "USDT"
    price = client.get_symbol_ticker(symbol=symbol_usdt)
    return float(price["price"])


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