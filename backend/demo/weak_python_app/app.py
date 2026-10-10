"""Toy Flask-style auth module — intentionally uses weak/legacy crypto for the demo."""
import hashlib
from Crypto.PublicKey import RSA


def hash_password(password: str) -> str:
    # Weak: MD5 has known collision attacks and is not quantum-relevant-safe either.
    return hashlib.md5(password.encode()).hexdigest()


def generate_signing_key():
    # Weak: RSA-1024 is both under-strength classically and fully broken by Shor's algorithm.
    return RSA.generate(1024)
