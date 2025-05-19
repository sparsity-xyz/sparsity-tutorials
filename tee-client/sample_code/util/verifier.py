import json
import base64

import cbor2
from pycose.messages import CoseMessage
from pycose.keys import EC2Key
from pycose.keys.keyops import VerifyOp
from pycose.keys.curves import P384
from pycose.algorithms import Es384
from OpenSSL import crypto
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import ec


class Verifier:
    @staticmethod
    def bytes_converter(obj):
        if isinstance(obj, bytes):
            return obj.hex()
        return str(obj)

    @staticmethod
    def verify_signature(pub_key: bytes, msg: bytes, signature: bytes) -> bool:
        pub_key = serialization.load_der_public_key(pub_key, backend=default_backend())
        try:
            pub_key.verify(signature, msg, ec.ECDSA(hashes.SHA384()))
            return True
        except:
            return False

    @staticmethod
    def verify_attestation(base64_att_doc: str, root_ca_path: str = "./root.pem") -> bool:
        """
        Verify an attestation document (base64 encoded).
        Steps:
        1. Decode and verify COSE signature using public key from the embedded certificate.
        2. Verify the certificate against the provided CA bundle and root cert.
        3. Verify the user_data is the hash of public key

        Returns True if valid, False otherwise.
        """
        # Step 1: Decode COSE
        attestation_bytes = base64.b64decode(base64_att_doc)
        tagged = cbor2.dumps(cbor2.CBORTag(18, cbor2.loads(attestation_bytes)))
        cose_msg = CoseMessage.decode(tagged)

        # Step 2: Extract payload and parse
        att_doc = cbor2.loads(cose_msg.payload)

        # Step 3: Extract certificate and construct COSE key
        cert_bytes = att_doc["certificate"]
        cert = x509.load_der_x509_certificate(cert_bytes, default_backend())
        pub_key = cert.public_key()
        pub_numbers = pub_key.public_numbers()
        x_bytes = pub_numbers.x.to_bytes(48, byteorder="big")
        y_bytes = pub_numbers.y.to_bytes(48, byteorder="big")

        cose_key = EC2Key(
            crv=P384,
            x=x_bytes,
            y=y_bytes,
            optional_params={"alg": Es384, "key_ops": [VerifyOp]},
        )

        # Step 4: Verify COSE signature
        cose_msg.key = cose_key
        if not cose_msg.verify_signature():
            return False

        # Step 5: Build cert chain and verify against CA bundle
        store = crypto.X509Store()
        for inter_der in att_doc.get("cabundle", []):
            inter_cert = crypto.load_certificate(crypto.FILETYPE_ASN1, inter_der)
            store.add_cert(inter_cert)

        # Load root CA
        with open(root_ca_path, "rb") as f:
            root_cert = crypto.load_certificate(crypto.FILETYPE_PEM, f.read())
            store.add_cert(root_cert)

        # Verify the certificate chain
        cert_obj = crypto.load_certificate(crypto.FILETYPE_ASN1, cert_bytes)
        store_ctx = crypto.X509StoreContext(store, cert_obj)
        try:
            store_ctx.verify_certificate()
        except Exception as e:
            # Allow expired cert if desired
            if "certificate has expired" not in str(e):
                return False

        # verify user_data
        digest = hashes.Hash(hashes.SHA256())
        digest.update(att_doc["public_key"])
        return digest.finalize() == att_doc["user_data"]

    @staticmethod
    def decode_attestation_dict(att_doc: str) -> dict:
        tagged = cbor2.dumps(cbor2.CBORTag(18, cbor2.loads(base64.b64decode(att_doc))))
        cose_msg = CoseMessage.decode(tagged)
        payload = cose_msg.payload
        return cbor2.loads(payload)

    @staticmethod
    def decode_attestation_str(att_doc: str) -> str:
        return json.dumps(Verifier.decode_attestation_dict(att_doc), indent=2, default=Verifier.bytes_converter)


if __name__ == '__main__':
    attestation_doc = "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"
    print(Verifier.decode_attestation_str(attestation_doc))
    print(Verifier.verify_attestation(attestation_doc))
    print(Verifier.verify_signature(
        pub_key=bytes.fromhex("3076301006072a8648ce3d020106052b8104002203620004548785a5e32ea9dac119ba171b2d831713b17ac9d024ab15aa087c421c4706f82d6d12908d391e958fc85594e6a1444fb2588ebf190669690babf4852e93c8b85993a5e1c8b9ee24251ad565729459a24c68575afde20a9f4e2085426b71fa58"),
        msg=json.dumps({"serverTime":1745481149237}).encode(),
        signature=bytes.fromhex("3066023100d768467983e34577bcb34b943f4195eda46f09debeb642a83bf674431b54a64aea90bb5c26e2639c1ee9350ea9c6e98d0231008a2cb16f47eae67919b5e9f8d6c78f03c526991ac85af9206ae3a74d0f94e0a24da7017178047e5f1dc47153102b0d1f"),
    ))
