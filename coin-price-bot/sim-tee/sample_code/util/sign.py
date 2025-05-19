import json
import os
from typing import Union

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


class Signer:
    def __init__(self, private_key: ec.EllipticCurvePrivateKey = None, public_key: ec.EllipticCurvePublicKey = None):
        if private_key is None:
            self.private_key = ec.generate_private_key(ec.SECP384R1())
            self.public_key = self.private_key.public_key()
        else:
            self.private_key = private_key
            self.public_key = public_key

    def get_public_key_der(self) -> bytes:
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def get_private_key_pem(self) -> str:
        """
        Export private key in PEM format (unencrypted).
        """
        return self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()

    def get_public_key_hash(self) -> bytes:
        """
        Hash the public key (PEM-encoded) using SHA-256.
        This can be used as user_data in attestation.
        """
        digest = hashes.Hash(hashes.SHA256())
        digest.update(self.get_public_key_der())
        return digest.finalize()

    def sign(self, message: Union[bytes, str, dict]) -> bytes:
        """
        Sign a message using the private key (ECDSA P-384 with SHA-384).
        """
        if isinstance(message, str):
            message = message.encode()
        elif isinstance(message, dict) or isinstance(message, list):
            message = json.dumps(message, separators=(
                ',', ':'), sort_keys=True).encode()
        elif not isinstance(message, bytes):
            raise TypeError("Message must be str, dict or bytes")

        return self.private_key.sign(
            message,
            ec.ECDSA(hashes.SHA384())
        )

    def encrypt(self, public_key: bytes, nonce: bytes, message: bytes) -> bytes:
        shared_key = self.private_key.exchange(
            ec.ECDH(), serialization.load_der_public_key(public_key))
        aes_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"encryption data"
        ).derive(shared_key)
        return AESGCM(aes_key).encrypt(nonce, message, None)

    def decrypt(self, public_key: bytes, nonce: bytes, data: bytes) -> bytes:
        # ECDH exchange key
        shared_key = self.private_key.exchange(
            ec.ECDH(), serialization.load_der_public_key(public_key))
        # derive AES key
        aes_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"encryption data"
        ).derive(shared_key)
        return AESGCM(aes_key).decrypt(nonce, data, associated_data=None)


if __name__ == '__main__':
    s1 = Signer()
    s2 = Signer()

    _message = b"Hello, world!"
    _nonce = os.urandom(32)
    _data = s1.encrypt(s2.get_public_key_der(), _nonce, _message)
    print(s2.decrypt(s1.get_public_key_der(), _nonce, _data))
