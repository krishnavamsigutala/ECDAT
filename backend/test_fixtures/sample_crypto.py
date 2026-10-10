import hashlib
from Crypto.Cipher import AES, DES
from Crypto.PublicKey import RSA

def weak_hash(data):
    return hashlib.md5(data).hexdigest()

def old_cipher(key, data):
    cipher = DES.new(key, DES.MODE_ECB)
    return cipher.encrypt(data)

def gen_key():
    return RSA.generate(1024)

def strong_cipher(key, nonce, data):
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.encrypt(data)
