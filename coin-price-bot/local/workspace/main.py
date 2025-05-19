import json
import os

import requests

from util.signer import Signer
from util.verifier import Verifier


class ClientRequest:
    tee_endpoint: str
    public_key: str = ""
    api_key: str
    att: dict

    def __init__(self):
        # TODO: Initialize the client with required environment variables
        # Hint: You need to get the API key, platform, and model from environment variables
        # Then set up the TEE endpoint URL and initialize the signer
        # Finally, initialize the keys
        pass

    def init_keys(self):
        # TODO: Initialize keys by verifying the attestation
        # Hint: If attestation verification fails, raise an exception
        # Otherwise, set the public_key from the attestation document
        pass

    def verify_attestation(self) -> bool:
        # Get the attestation document from the TEE endpoint
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

    def chat(self, message: str):
        # TODO: Implement the chat functionality that sends a message to the TEE endpoint
        # Hint: Prepare the data with API key, message, platform, and model
        # Generate a nonce and encrypt the data using the signer
        # Make a POST request to "{tee_endpoint}/talk" with the encrypted data
        # Verify the signature of the response and return the final response
        pass

    def verify_sig(self, data, sig) -> bool:
        # TODO: Implement signature verification
        # Hint: Use the Verifier to verify the signature with the public key
        pass


if __name__ == '__main__':
    client = ClientRequest()
    client.chat("BTC price right now")