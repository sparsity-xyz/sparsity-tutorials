# Secure AI Agent TEE Tutorial (tee-tls Framework)

This tutorial will guide you through implementing the two core functions needed for a secure AI agent running inside a TEE, using the tee-tls framework. You will:
- Implement `create_toolkit_and_run` and `talk_to_ai` in `enclave/app.py`
- Enable secure, attested AI chat via the TEE

---

## Sidenote: Prerequisites & Tools
- This project assumes you are already familiar with Docker, dnsmasq, and the basic TEE-tls container setup.
- All DNS routing, container networking, and peripheral setup (dnsmasq, entrypoint, etc.) are already handled for you.
- If you need a refresher, see the sample_code or previous tutorials.

---

## 1. Implement `create_toolkit_and_run` in `enclave/app.py`

Open `enclave/app.py` and find the `create_toolkit_and_run` method. Your task is to implement this function so that it:

- Creates a toolkit using the provided session (see `create_toolkit` from the MCP module)
- Initializes an AssistantAgent with the user's API key and the correct LLMConfig (model, api_type, api_key)
- Runs the agent with the user's message and the toolkit's tools
- Processes the result and returns it

**Example Implementation:**
```python
async def create_toolkit_and_run(self, session: ClientSession, api_key: str, message: str):
    toolkit = await create_toolkit(session=session)
    agent = AssistantAgent(
        name="assistant",
        llm_config=LLMConfig(model="gpt-4o-mini", api_type="openai", api_key=api_key)
    )
    result = await agent.a_run(
        message=message,
        tools=toolkit.tools,
        max_turns=2,
        user_input=False,
    )
    await result.process()
    return result
```
See also: `agent-mcp/sim-tee/sample_code/enclave/app.py` for further details.

---

## 2. Implement `talk_to_ai` in `enclave/app.py`

Find the `talk_to_ai` method. This is the main endpoint for processing encrypted chat requests. Implement it so that it:

- Validates the nonce and extracts the public key and encrypted data from the request
- Decrypts the data using the key manager (`self.key.decrypt`)
- Parses the decrypted data into a `ChatData` object
- Validates that the API key and model are provided
- Sets up the stdio connection with the correct parameters (see `StdioServerParameters`)
- Creates a session, initializes it, and runs the toolkit using your `create_toolkit_and_run` function
- Gets the messages from the result and returns a signed response using `self.response()`

**Example Implementation:**
```python
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

    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py", "stdio"],
    )

    async with stdio_client(server_params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        result = await self.create_toolkit_and_run(session, chat_data.api_key, chat_data.message)

    messages = await result.messages
    return self.response(messages)
```
See also: `agent-mcp/sim-tee/sample_code/enclave/app.py` for further details.

---

## 3. How to Run and Test

Follow these steps to run and test your implementation:

1. **Start the host proxy/server:**
   ```bash
   make run-host
   ```
2. **Build and run the ag2-mcp (TEE) container:**
   ```bash
   make build-ag2-mcp && make run-ag2-mcp-local
   ```
3. **Run the client to interact with the setup:**
   - In a new terminal, go to the `client` directory:
     ```bash
     cd agent-mcp/sim-tee/client
     ```
   - Set the required environment variables as described in `README.md`:
     ```bash
     export PYTHONPATH="$PYTHONPATH:$PWD"
     export PLATFORM_API_KEY=<openai_api_key>
     export PLATFORM=openai
     export MODEL=gpt-4
     export TEE_TLS_URL=http://localhost:8000/
     ```
   - Run the client:
     ```bash
     python3 main.py
     ```

See `client/README.md` for more details on the environment variables and client usage.

---

## 4. Reference
- For API and class details, see the sample_code and the tee-tls framework documentation.
- For peripheral setup (dnsmasq, Docker, etc.), refer to previous tutorials or the provided Makefile and Dockerfile.

---

**Your goal:** Implement only the two functions above. All other infrastructure is already in place. Good luck! 