#ifndef TRANSACTION_H
#define TRANSACTION_H

#include <cstddef>
#include <cstdint>
#include "wallet.h"
#include "export.h"

#define ADDRESS_SIZE 65

#define TX_SERIALIZED_SIZE (ADDRESS_SIZE + ADDRESS_SIZE + sizeof(uint64_t))

struct Transaction {
	char sender[ADDRESS_SIZE];
	char receiver[ADDRESS_SIZE];
	uint64_t amount;
	unsigned char signature[SIGNATURE_SIZE];
};

void serialize_transaction(const Transaction* tx, char* buffer, size_t buffer_size);
Transaction create_coinbase_transaction(const char* receiver, uint64_t reward);

BLOCKCHAIN_API int sign_transaction(Transaction* tx, const unsigned char* private_key);
BLOCKCHAIN_API int sign_transaction_raw(const char* sender, const char* receiver, uint64_t amount, 
const unsigned char* private_key, unsigned char* signature_out);

BLOCKCHAIN_API int verify_transaction_signature(const Transaction* tx);
BLOCKCHAIN_API int verify_transaction_signature_raw(const char* sender, const char* receiver, uint64_t amount, const unsigned char* signature);

#endif // !TRANSACTION_H
