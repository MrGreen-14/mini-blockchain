#include "transaction.h"
#include <cstdio>

void serialize_transaction(const Transaction* tx, char* buffer, size_t buffer_size) {
	snprintf(buffer, buffer_size, "%s%s%llu", tx->sender, tx->receiver,(unsigned long long)tx->amount);
}