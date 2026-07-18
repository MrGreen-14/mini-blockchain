#include "transaction.h"
#include <cstdio>
#include <string.h>



void serialize_transaction(const Transaction* tx, char* buffer, size_t buffer_size) {
	snprintf(buffer, buffer_size, "%s%s%llu", tx->sender, tx->receiver,(unsigned long long)tx->amount);
}

Transaction create_coinbase_transaction(const char* receiver, uint64_t reward) {
	Transaction tx;
	memset(&tx, 0, sizeof(Transaction));
	strncpy(tx.sender, "COINBASE", ADDRESS_SIZE - 1);
	strncpy(tx.receiver, receiver, ADDRESS_SIZE - 1);
	tx.amount = reward;
	return tx;
}