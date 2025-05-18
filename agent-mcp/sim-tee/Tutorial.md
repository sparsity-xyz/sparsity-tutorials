# Secure AI Agent with TEE Simulation Tutorial

In this tutorial, you'll learn how to implement key functions in a Trusted Execution Environment (TEE) that processes encrypted requests for an AI chatbot. You'll work with the `app.py` file located in the `agent-mcp/sim-tee/workplace/enclave` directory.

## Prerequisites

- Familiarity with Python and asynchronous programming
- Basic understanding of cryptography concepts
- Knowledge of FastAPI for building APIs
- Understanding of AutoGen for agent-based AI applications

## Getting Started

Before diving into the implementation, let's set up and run the example project:

### Running the Project

You can execute the entire project using the provided Makefile commands. Navigate to the `sample_code` directory and run the following commands:

```bash
# Start the host server
make run-host

# In a new terminal, build and run the MCP agent
make build-ag2-mcp && make run-ag2-mcp-local
```

These commands work across most platforms (Linux, macOS, WSL). They will:
1. Start the TEE host server that will forward encrypted requests/responses
2. Build and run the AutoGen MCP agent that provides the toolkit functionality

Once both services are running, you can interact with the system by sending encrypted requests to the TEE endpoint.

### Running the Client

To test the TEE server, you'll need to run a client that sends encrypted messages. Navigate to the `agent-mcp/sim-tee/client` directory and follow these steps:

1. Install the client requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up the necessary environment variables:
   ```bash
   export PYTHONPATH="$PYTHONPATH:$PWD"
   export PLATFORM_API_KEY=<your_openai_api_key>
   export PLATFORM=openai
   export MODEL=gpt-4
   export TEE_TLS_URL=http://127.0.0.1:8000/  # For local testing
   ```
   Note: Replace `<your_openai_api_key>` with your actual OpenAI API key.

3. Run the client:
   ```bash
   python3 main.py
   ```

The client will:
1. Generate a random nonce
2. Encrypt your message using the TEE's public key
3. Send the encrypted request to the TEE server
4. Receive, verify, and display the response

This allows you to test the complete flow of secure message exchange with the TEE server you've implemented.

## Project Overview

This project simulates a secure endpoint that:

1. Receives encrypted requests with user prompts
2. Validates and decrypts these requests
3. Processes them securely within a TEE
4. Leverages AutoGen to create AI agents and toolkits
5. Returns signed responses to ensure authenticity

## Understanding the Codebase Structure

### Key Components of app.py

- **ChatRequest**: Pydantic model defining the structure of incoming encrypted requests
- **ChatData**: Dataclass for decrypted message data
- **APP**: Main application class that handles endpoints and request processing
- **FixedKeyManager/MockFixedKeyManager**: Utilities for encryption/decryption and attestation

### API Endpoints

- `/ping`: Simple health check endpoint
- `/attestation`: Provides attestation document to verify the TEE's identity
- `/query`: Test endpoint for querying external services
- `/talk`: Main endpoint for sending encrypted messages to the AI

### Your Implementation Tasks

You need to implement two critical methods:

1. `create_toolkit_and_run`: Creates and runs an AutoGen agent with tools
2. `talk_to_ai`: Processes encrypted requests and manages the session

## Detailed Implementation Guide

### Task 1: Implementing `create_toolkit_and_run`

This method creates a toolkit with tools for the AI agent and runs it with the user's message.

```python
async def create_toolkit_and_run(self, session: ClientSession, api_key: str, message: str):
    # Create a toolkit using the session
    toolkit = await create_toolkit(session=session)
    
    # Initialize an AI assistant agent with the provided API key
    agent = AssistantAgent(
        name="assistant", 
        llm_config=LLMConfig(
            model="gpt-4o-mini", 
            api_type="openai",
            api_key=api_key
        )
    )

    # Run the agent with the user's message and toolkit
    result = await agent.a_run(
        message=message,
        tools=toolkit.tools,
        max_turns=2,  # Limit conversation turns
        user_input=False,  # Don't request additional user input
    )
    
    # Process the result
    await result.process()
    
    return result
```

Let's break down what this method does:

1. **Creating a Toolkit**: The `create_toolkit` function from AutoGen's MCP module creates a toolkit with various tools that the agent can use. The toolkit is created using the provided session.

2. **Initializing the Agent**: An `AssistantAgent` is created with:
   - A name ("assistant")
   - LLM configuration including the model to use ("gpt-4o-mini")
   - API type ("openai")
   - The user's API key passed from the decrypted request

3. **Running the Agent**: The agent is run asynchronously with:
   - The user's message
   - The tools from the toolkit
   - A limit on conversation turns (2)
   - User input disabled (the TEE processes the request without further interaction)

4. **Processing the Result**: The result is processed and returned for further handling

### Task 2: Implementing `talk_to_ai`

This method handles the main endpoint for AI interaction, including decryption of requests and session management.

```python
async def talk_to_ai(self, req: ChatRequest):
    # Extract and validate request parameters
    nonce = bytes.fromhex(req.nonce)
    if len(nonce) < 8:
        return JSONResponse({"error": "invalid nonce, must be at least 8 characters long"})

    # Extract the public key and encrypted data
    public_key = bytes.fromhex(req.public_key)
    data = bytes.fromhex(req.data)

    # Decrypt the data using the key manager
    raw_data = self.key.decrypt(public_key, nonce, data)
    
    # Parse the decrypted data into a ChatData object
    chat_data = ChatData(**json.loads(raw_data))
    
    # Validate required fields
    if chat_data.api_key == "":
        return JSONResponse({"error": "empty api_key"})
    elif chat_data.ai_model == "":
        return JSONResponse({"error": "empty ai_model"})
    
    # Set up stdio connection parameters
    server_params = StdioServerParameters(
        command="python",  # Command to run the server
        args=[
            str("mcp_server.py"),
            "stdio",
        ],  # Path to server script and transport mode
    )

    # Create a session, initialize it, and run the toolkit
    async with stdio_client(server_params) as (read, write), ClientSession(read, write) as session:
        # Initialize the connection
        await session.initialize()
        
        # Set up tools and agent
        result = await self.create_toolkit_and_run(session, chat_data.api_key, chat_data.message)
    
    # Get the messages from the result
    messages = await result.messages
    logger.info(messages)

    # Return a signed response
    return self.response(messages)
```

Let's break down what this method does:

1. **Input Validation**:
   - Extracts and validates the nonce (must be at least 8 bytes)
   - Extracts the public key and encrypted data

2. **Decryption and Parsing**:
   - Uses the key manager to decrypt the data using the provided public key and nonce
   - Parses the decrypted data into a `ChatData` object

3. **Field Validation**:
   - Ensures the API key is not empty
   - Ensures the AI model is specified

4. **Setting Up the Connection**:
   - Creates parameters for a stdio connection
   - Specifies the command to run the server and its arguments

5. **Session Management**:
   - Creates a stdio client connection
   - Initializes a ClientSession for communication
   - Initializes the connection

6. **Processing the Request**:
   - Calls the `create_toolkit_and_run` method with the session, API key, and message
   - Retrieves the messages from the result

7. **Response Generation**:
   - Logs the messages
   - Creates and returns a signed response using the `response` method

## Testing Your Implementation

Once you've implemented both methods, you can test your TEE simulation by:

1. Starting the server:
   ```bash
   python app.py
   ```

2. Sending encrypted requests to the `/talk` endpoint with the proper format:
   ```
   {
       "nonce": "<hex_encoded_nonce>",
       "public_key": "<hex_encoded_public_key>",
       "data": "<hex_encoded_encrypted_data>"
   }
   ```

The server will:
1. Decrypt the request
2. Process it using the AI agent and tools
3. Return a signed response

## Understanding the Secure Flow

This implementation demonstrates a secure TEE-based AI interaction flow:

1. **Client-Side**:
   - Generates a random nonce
   - Encrypts the message with the TEE's public key
   - Sends the encrypted request

2. **Server-Side (Your Implementation)**:
   - Validates and decrypts the request
   - Processes it in the secure environment
   - Signs the response for verification

3. **Security Benefits**:
   - Messages are encrypted in transit
   - API keys are protected within the TEE
   - Responses are signed to prevent tampering

## Conclusion

By implementing these methods, you've created a secure endpoint for AI interactions that protects user data and API keys. This pattern can be extended to various secure AI applications, especially those requiring protection of sensitive data or credentials.

The TEE simulation demonstrates the principles of confidential computing, where sensitive operations occur in a protected environment isolated from the main operating system. In a production environment, this would be complemented with proper attestation verification to ensure the code hasn't been tampered with. 