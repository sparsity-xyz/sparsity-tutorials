# Secure Communication with Trusted Execution Environment (TEE) Tutorial

This tutorial will guide you through implementing a client application that communicates securely with a Trusted Execution Environment (TEE) endpoint for chatbot requests. You'll learn how to establish secure communication, verify TEE attestation, and encrypt/decrypt messages.

## Prerequisites

- Basic understanding of cryptography concepts
- Familiarity with Python programming
- Understanding of REST API calls

## Working Environment

For this tutorial, you'll be working in the `tee-tee-tls/local/workspace` directory. This directory contains the necessary utility files and skeleton code that you'll be implementing.

## Project Structure

- `main.py`: This is where you'll implement the `ClientRequest` class
- `util/`: Directory containing helper utilities:
  - `signer.py`: Provides encryption and signing capabilities
  - `verifier.py`: Offers verification functionality for attestation and signatures
- `requirements.txt`: Lists the required dependencies

## What is TEE?

A Trusted Execution Environment (TEE) is a secure area inside a processor that ensures confidentiality and integrity of code and data loaded inside it. By using a TEE, you can be confident that sensitive operations are executed in a protected environment isolated from the main operating system.

## Setup

Before we begin coding, ensure you have the required dependencies installed:

```bash
pip install -r requirements.txt
```

You'll also need to set the following environment variables:

```bash
export PLATFORM_API_KEY="your_api_key"
export PLATFORM="your_platform"
export MODEL="your_model"
export TEE_TLS_URL="http://127.0.0.1:8000"  # Default for local testing
```

## Implementation Guide

In this tutorial, you'll implement the `ClientRequest` class in `main.py`. The class handles secure communication with a TEE endpoint. We'll go through each method step by step.

### Step 1: Constructor Initialization

The first method to implement is `__init__`. This method initializes the client with the necessary environment variables and sets up the signer.

```python
def __init__(self):
    self.api_key = os.getenv("PLATFORM_API_KEY")
    self.platform = os.getenv("PLATFORM")
    self.model = os.getenv("MODEL")
    if not self.api_key:
        raise Exception('API key is required')
    self.tee_endpoint = os.getenv("TEE_TLS_URL", "http://127.0.0.1:8000")
    self.signer = Signer()
    self.init_keys()
```

### Step 2: Initializing Keys

Next, implement the `init_keys` method to verify attestation and set the public key:

```python
def init_keys(self):
    if not self.verify_attestation():
        raise Exception('Attestation failed')
    self.public_key = self.att["public_key"].hex()
```

### Step 3: Verifying Attestation

The `verify_attestation` method is crucial for ensuring you're communicating with a genuine TEE:

```python
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

### Step 4: Implementing the Chat Method

The `chat` method handles message encryption and sending to the TEE endpoint:

```python
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
    print("request:", req)
    resp = requests.post(f"{self.tee_endpoint}/talk", json=req).json()

    print()
    print('prompt:', message)
    print("response_raw: ", resp)
    print("final response:", resp["data"]["response"])
    print("verify signature:", self.verify_sig(resp["data"], resp["sig"]))
```

### Step 5: Signature Verification

Finally, implement the `verify_sig` method to verify response signatures:

```python
def verify_sig(self, data, sig) -> bool:
    return Verifier.verify_signature(
        pub_key=bytes.fromhex(self.public_key),
        msg=json.dumps(data).encode(),
        signature=bytes.fromhex(sig),
    )
```

## Understanding the Flow

1. **Attestation Verification**: Before any communication, the client verifies the TEE's identity by checking its attestation document.
2. **Secure Communication**:
   - Client encrypts the message with the TEE's public key
   - Client sends the encrypted message to the TEE
   - TEE decrypts the message, processes it, and sends back an encrypted response
   - Client verifies the signature of the response and decrypts it

## Testing Your Implementation

After implementing all the methods, you can test your client by running:

```bash
python main.py
```

This will send a sample query "BTC price right now" to the TEE endpoint.

## Conclusion

In this tutorial, you've learned how to implement secure communication with a TEE endpoint. You've built a client that:
- Verifies the identity of a TEE using attestation
- Establishes secure communication using encrypted channels
- Sends encrypted messages and verifies signed responses

This approach ensures that sensitive data remains protected during transmission and processing, which is essential for applications requiring high security and privacy guarantees.