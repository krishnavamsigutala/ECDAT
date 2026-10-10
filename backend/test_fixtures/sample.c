#include <openssl/rsa.h>
#include <openssl/sha.h>
#include <openssl/des.h>

void gen() {
    RSA *rsa = RSA_generate_key(2048, 65537, NULL, NULL);
}

void hash_it() {
    SHA256_CTX ctx;
    SHA256_Init(&ctx);
}

void weak() {
    DES_cblock key;
    DES_key_schedule schedule;
    DES_set_key(&key, &schedule);
}
