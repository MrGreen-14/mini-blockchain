#ifndef SHA256_WRAPPER_H
#define SHA256_WRAPPER_H

#include <stddef.h>
#include "export.h"

BLOCKCHAIN_API void compute_sha256_hex(const unsigned char* data, size_t lenght, char output_hex[65]);

BLOCKCHAIN_API void compute_sha256_raw(const unsigned char* data, size_t lenght,
	unsigned char output_raw[32]);

#endif