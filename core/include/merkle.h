#ifndef MERKLE_H
#define MERKLE_H

#include "transaction.h"
#include <cstdio>

void compute_merkle_root(const Transaction* transactions, size_t count, char output_hex[65]);

#endif
