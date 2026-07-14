#include "sha256.h"
#include <openssl/sha.h>
#include <stdio.h>

void compute_sha256_hex(const unsigned char* data, size_t lenght, char output_hex[65]) {
	unsigned char digest[SHA256_DIGEST_LENGTH];
	SHA256(data, lenght, digest);

	for (int i = 0; i < SHA256_DIGEST_LENGTH; i++){
		sprintf(output_hex + (i * 2), "%02x", digest[i]);
	}
	output_hex[64] = '\0';
}