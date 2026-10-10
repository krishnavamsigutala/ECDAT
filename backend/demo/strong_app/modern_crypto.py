"""Modern reference implementation — used as a 'good' contrast example in the demo."""
from Crypto.Cipher import AES
import hashlib


def encrypt(key: bytes, nonce: bytes, data: bytes) -> bytes:
    # Strong (for now): AES-256-GCM retains a 128-bit security margin under Grover's algorithm.
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.encrypt(data)


def fingerprint(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
