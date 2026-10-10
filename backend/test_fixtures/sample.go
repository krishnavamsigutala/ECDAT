package main

import (
    "crypto/rsa"
    "crypto/sha256"
)

func main() {
    _ = rsa.PublicKey{}
    _ = sha256.New()
}
