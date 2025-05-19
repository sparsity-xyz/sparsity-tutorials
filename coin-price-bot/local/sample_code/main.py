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
        self.api_key = os.getenv("PLATFORM_API_KEY")
        self.platform = os.getenv("PLATFORM")
        self.model = os.getenv("MODEL")
        if not self.api_key:
            raise Exception('API key is required')
        self.tee_endpoint = os.getenv("TEE_TLS_URL", "http://127.0.0.1:8000")
        self.signer = Signer()
        self.init_keys()

    def init_keys(self):
        if not self.verify_attestation():
            raise Exception('Attestation failed')
        self.public_key = self.att["public_key"].hex()

    def verify_attestation(self) -> bool:
        att = requests.get(f"{self.tee_endpoint}/attestation").json()
        # print('Verifying attestation document:')
        # print('attestation document = ', att)
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
            # print("attestation verification result:", result)
            print("Verifying TEE Enclave Identity:", result)
            return result

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

    def verify_sig(self, data, sig) -> bool:
        return Verifier.verify_signature(
            pub_key=bytes.fromhex(self.public_key),
            msg=json.dumps(data).encode(),
            signature=bytes.fromhex(sig),
        )


if __name__ == '__main__':
    client = ClientRequest()
    client.chat("BTC price right now")
