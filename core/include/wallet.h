#ifndef WALLET_H
#define WALLET_H

#include <cstdint>
#include <cstddef>
#include "export.h"

#define PRIVATE_KEY_SIZE 32

#define PUBLIC_KEY_SIZE 65

#define SIGNATURE_SIZE 64  // r (32) + s (32)


BLOCKCHAIN_API int generate_keypair(unsigned char* private_key_out,
	unsigned char* public_out_key);

BLOCKCHAIN_API int sign_hash(const unsigned char* private_key, const unsigned char hash[32], unsigned char* signature_out);
BLOCKCHAIN_API int verify_hash_signature(const unsigned char* public_key, const unsigned char hash[32], const unsigned char* signature);

#endif