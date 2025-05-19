# Secure Communication with Trusted Execution Environment (TEE) Tutorial

This tutorial will guide you through implementing a client application that communicates securely with a Trusted Execution Environment (TEE) endpoint for chatbot requests. You'll learn how to establish secure communication, verify TEE attestation, and encrypt/decrypt messages.

## Prerequisites

- Basic understanding of cryptography concepts
- Familiarity with Python programming
- Understanding of REST API calls

## Working Environment

For this tutorial, you'll be working in the `tee-client/workspace` directory. This directory contains the necessary utility files and skeleton code that you'll be implementing.

## Project Structure

- `client.py`: This is where you'll implement the `ClientRequest` class.
- `util/`: Directory containing helper utilities:
  - `signer.py`: Provides encryption and signing capabilities.
  - `verifier.py`: Offers verification functionality for attestation and signatures.
  - `root.pem`: Root certificate for attestation verification (ensure this is present in `workspace/util/`).
- `requirements.txt`: Lists the required dependencies.

## What is TEE?

A Trusted Execution Environment (TEE) is a secure area inside a processor that ensures confidentiality and integrity of code and data loaded inside it. By using a TEE, you can be confident that sensitive operations are executed in a protected environment isolated from the main operating system.

## Setup

Before we begin coding, ensure you have the required dependencies installed (usually by running `pip install -r requirements.txt` in the `workspace` directory).

You'll also need to set the following environment variables:

```bash
export PLATFORM_API_KEY="your_api_key"
export PLATFORM="your_platform" # e.g., openai
export MODEL="your_model"       # e.g., gpt-4
export TEE_TLS_URL="http://127.0.0.1:8000"  # Default endpoint for local testing
```

You can check the connection to the TEE_TLS_URL by querying the following endpoint: `http://127.0.0.1:8000/attestation`, which will output something like the following:
```
{"attestation_doc":"hEShATgioFkR76lpbW9kdWxlX2lkeCdpLTA5NzM5OTQ3MWYxOWRmZWMzLWV..."}
```

## Implementation Guide

In this tutorial, you'll complete the `ClientRequest` class in `client.py`. The class handles secure communication with a TEE endpoint. We'll go through each method step by step, using the versions in `tee-client/sample_code/client.py` and `sample_code/main.py` as a reference for the completed code.

### Step 1: Constructor Initialization (`__init__`)

The `__init__` method initializes the client. Your `client.py` might already have this partially filled. Ensure it correctly:
1. Retrieves `PLATFORM_API_KEY`, `PLATFORM`, and `MODEL` from environment variables.
2. Raises an exception if `PLATFORM_API_KEY` is missing.
3. Stores the `tee_endpoint` (passed as an argument, defaulting to `http://127.0.0.1:8000` for local testing).
4. Initializes a `Signer` instance: `self.signer = Signer()`.
5. **Crucially, calls `self.init_keys()` at the end to set up cryptographic keys.**

```python
# Target for __init__ in client.py
def __init__(self, tee_endpoint: str = "http://127.0.0.1:8000"):
    self.api_key = os.getenv("PLATFORM_API_KEY")
    self.platform = os.getenv("PLATFORM")
    self.model = os.getenv("MODEL")
    if not self.api_key:
        raise Exception('API key is required')
    self.tee_endpoint = tee_endpoint
    self.signer = Signer()
    self.init_keys() # Important: Call to initialize keys
```

### Step 2: Initializing Keys (`init_keys`)

This method is responsible for performing TEE attestation and setting the TEE's public key. Implement it in `client.py`:

```python
# To be implemented in client.py
def init_keys(self):
    if not self.verify_attestation():
        raise Exception('Attestation failed')
    self.public_key = self.att["public_key"].hex()
```
This method calls `verify_attestation()`. If successful, it stores the TEE's public key (obtained from the attestation document) in `self.public_key`.

### Step 3: Verifying Attestation (`verify_attestation`)

This method fetches and verifies the TEE's attestation document. This is crucial for ensuring you're communicating with a genuine TEE. Implement this in `client.py`:

```python
# To be implemented in client.py
def verify_attestation(self) -> bool:
    att = requests.get(f"{self.tee_endpoint}/attestation").json()
    if att.get("mock"):
        self.att = {
            "public_key": bytes.fromhex(att["attestation_doc"]["public_key"]),
        }
        print("attestation verification result: mock true")
        return True
    else:
        att = att["attestation_doc"]
        self.att = Verifier.decode_attestation_dict(att)
        result = Verifier.verify_attestation(att, "./util/root.pem")
        print("Verifying TEE Enclave Identity:", result)
        return result
```
This method:
1. Fetches the attestation document from the TEE's `/attestation` endpoint.
2. Handles a "mock" attestation for local testing.
3. For real attestations, it decodes the document and verifies it against a root CA certificate (`./util/root.pem`). Make sure this file exists in `workspace/util/`.

### Step 4: Implementing the Chat Method (`chat`)

The `chat` method encrypts the user's message and sends it to the TEE. It then processes and displays the TEE's response. Implement this in `client.py`:

```python
# To be implemented in client.py
def chat(self, message: str):
    data = {
        "api_key": self.api_key,
        "message": message,
        "platform": self.platform,
        "ai_model": self.model,
    }

    nonce = os.urandom(32)

    req = {
        "nonce": nonce.hex(),
        "public_key": self.signer.get_public_key_der().hex(),
        "data": self.signer.encrypt(bytes.fromhex(self.public_key), nonce, json.dumps(data).encode()).hex()
    }
    resp = requests.post(f"{self.tee_endpoint}/talk", json=req).json()

    print()
    print('prompt:', message)
    print("raw response: ", resp)
    print("verify signature:", self.verify_sig(resp["data"], resp["sig"]))

    return resp
```

### Step 5: Signature Verification (`verify_sig`)

This method verifies the digital signature of the TEE's response. Your `client.py` already has an implementation for this, but ensure it correctly serializes the `data` part for verification, as the server signs the JSON string of the `data` object.

```python
# To be implemented/corrected in client.py
def verify_sig(self, data, sig) -> bool:
    return Verifier.verify_signature(
        pub_key=bytes.fromhex(self.public_key),
        msg=data,
        signature=bytes.fromhex(sig),
    )
```

### Step 6: Using the Provided Main Script for Execution (`main.py`)

A `main.py` script is already provided in your workspace directory. This script is responsible for:

- Importing your `ClientRequest` class from `client.py`
- Initializing the client with the correct TEE endpoint
- Handling user input or command-line arguments for the prompt
- Calling the `chat` method to send the prompt to the TEE

**Do not add any `if __name__ == '__main__':` block to `client.py`.**
Keep your class implementation and your script entry point (`main.py`) separate for clarity and maintainability.

To run your client, simply use:

```bash
python main.py
```

## Understanding the Flow

1. **Attestation Verification**: The client verifies the TEE's identity.
2. **Secure Communication**: Messages are encrypted for the TEE, and TEE responses are signed.

## Testing Your Implementation

After implementing all the methods in `tee-client/workspace/client.py`, you can test it by running:

```bash
export PYTHONPATH="$PYTHONPATH:$(pwd)"
python main.py # edit the prompt inside main.py
```
Or, for interactive mode:
```bash
export PYTHONPATH="$PYTHONPATH:$(pwd)"
python main.py
```

If you are testing in the sample_code directory, make sure to set PYTHONPATH accordingly:
```bash
cd tee-client/sample_code
export PYTHONPATH="$PYTHONPATH:$(pwd)"
python main.py
```

## Conclusion

This tutorial guided you through implementing a secure TEE client. This ensures sensitive data (like API keys or prompts) is protected during communication with a TEE.