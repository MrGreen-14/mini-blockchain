#ifndef SHA256_WRAPPER_H
#define SHA256_WRAPPER_H

#include <stddef.h>

void compute_sha256_hex(const unsigned char* data, size_t lenght, char output_hex[65]);

#endif