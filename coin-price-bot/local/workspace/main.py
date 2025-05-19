import os

from client import ClientRequest

if __name__ == '__main__':
    # Get TEE_TLS_URL from environment variable, use default value if not set
    tee_endpoint = os.getenv("TEE_TLS_URL", "http://127.0.0.1:8000")
    client = ClientRequest(tee_endpoint=tee_endpoint)

    # Example usage with token query agent
    client.chat("Bitcoin Price today right now")

    # Example usage with general chat agent
    # client.chat("Hello")
    # client.chat("What's the date today")
