import os
import base64

from util.log import logger
from util.sign import Signer

try:
    import libnsm
except ImportError:
    libnsm = None


class EnclaveKeyManager(Signer):
    DOC_MAX_SIZE = 16 * 1024
    fd: int

    def __init__(self):
        # Generate ECDSA P-384 key pair
        super().__init__()

        self.load_nsm()

    def load_nsm(self):
        self.fd = libnsm.nsm_lib_init()

    def generate_attestation(self, nonce: bytes = b"") -> str:
        public_key = self.get_public_key_der()
        user_data = self.get_public_key_hash()

        result = libnsm.nsm_get_attestation_doc(
            self.fd,
            user_data,
            len(user_data),
            nonce,
            len(nonce),
            public_key,
            len(public_key)
        )
        return base64.b64encode(result).decode()


class FixedKeyManager(EnclaveKeyManager):
    nonce: bytes
    fixed_document: str

    def __init__(self, nonce=None):
        if nonce is None:
            self.nonce = b"tee-tls" + os.urandom(32)
            logger.info(f"Use fixed nonce: {self.nonce}")
        else:
            self.nonce = nonce
        super().__init__()
        self.fixed_document = self.generate_attestation(self.nonce)


class MockFixedKeyManager(FixedKeyManager):
    nonce: bytes
    fixed_document: dict

    def load_nsm(self):
        pass

    def generate_attestation(self, nonce: bytes = b"") -> dict:
        return {
            "nonce": nonce.hex(),
            "public_key": self.get_public_key_der().hex()
        }


if __name__ == '__main__':
    FixedKeyManager()

