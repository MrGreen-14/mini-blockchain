#ifndef TRANSACTION_H
#define TRANSACTION_H

#include <cstddef>
#include <cstdint>

#define ADDRESS_SIZE 65

struct Transaction {
	char sender[ADDRESS_SIZE];
	char receiver[ADDRESS_SIZE];
	uint64_t amount;
};

void serialize_transaction(const Transaction* tx, char* buffer, size_t buffer_size);

Transaction create_coinbase_transaction(const char* receiver, uint64_t reward);

#endif // !TRANSACTION_H
