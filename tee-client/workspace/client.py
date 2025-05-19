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

    def __init__(self, tee_endpoint: str = "http://127.0.0.1:8000"):
        self.api_key = os.getenv("PLATFORM_API_KEY")
        self.platform = os.getenv("PLATFORM")
        self.model = os.getenv("MODEL")
        if not self.api_key:
            raise Exception('API key is required')
        self.tee_endpoint = tee_endpoint
        self.signer = Signer()
        self.init_keys()

    def init_keys(self):
        # TODO: Implement key initialization
        pass

    def verify_attestation(self) -> bool:
        # TODO: Implement attestation verification
        pass

    def chat(self, message: str):
        # TODO: Implement multi-step chat method
        pass

    def verify_sig(self, data, sig) -> bool:
        return Verifier.verify_signature(
            pub_key=bytes.fromhex(self.public_key),
            msg=data,
            signature=bytes.fromhex(sig),
        )
