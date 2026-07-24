#include "transaction.h"
#include "sha256.h"
#include "wallet.h"
#include <cstdio>
#include <string.h>



void serialize_transaction(const Transaction* tx, char* buffer, size_t buffer_size) {
	if (buffer_size < TX_SERIALIZED_SIZE) return;
	
	size_t offset = 0;
	memcpy(buffer + offset, tx->sender, ADDRESS_SIZE);
	offset += ADDRESS_SIZE;
	memcpy(buffer + offset, tx->receiver, ADDRESS_SIZE);
	offset += ADDRESS_SIZE;
	memcpy(buffer + offset, &tx->amount, sizeof(tx->amount));
}

Transaction create_coinbase_transaction(const char* receiver, uint64_t reward) {
	Transaction tx;
	memset(&tx, 0, sizeof(Transaction));
	strncpy(tx.sender, "COINBASE", ADDRESS_SIZE - 1);
	strncpy(tx.receiver, receiver, ADDRESS_SIZE - 1);
	tx.amount = reward;
	return tx;
}

int sign_transaction(Transaction* tx, const unsigned char* private_key) {
	char buffer[TX_SERIALIZED_SIZE];
	serialize_transaction(tx, buffer, sizeof(buffer));

	unsigned char hash[32];
	compute_sha256_raw((const unsigned char*)buffer, TX_SERIALIZED_SIZE, hash);//secp256k1

	return sign_hash(private_key, hash, tx->signature);
}

int sign_transaction_raw(const char* sender, const char* receiver, uint64_t amount,
	const unsigned char* private_key, unsigned char* signature_out) {
	Transaction tx;
	memset(&tx, 0, sizeof(tx));
	memcpy(tx.sender, sender, ADDRESS_SIZE);
	memcpy(tx.receiver, receiver, ADDRESS_SIZE);
	tx.amount = amount;

	if (!sign_transaction(&tx, private_key))return 0;

	memcpy(signature_out, tx.signature, SIGNATURE_SIZE);
	return 1;
}

int verify_transaction_signature(const Transaction* tx) {
	char buffer[TX_SERIALIZED_SIZE];
	serialize_transaction(tx, buffer, sizeof(buffer));

	unsigned char hash[32];
	compute_sha256_raw((const unsigned char*)buffer, TX_SERIALIZED_SIZE, hash);

	// sender-ul = cheia publica bruta (ADDRESS_SIZE == PUBLIC_KEY_SIZE == 65)
	// nu exista un pas separat de "cauta adresa in registru", adresa e cheia.
	return verify_hash_signature((const unsigned char*)tx->sender, hash, tx->signature);
}

int verify_transaction_signature_raw(const char* sender, const char* receiver, uint64_t amount, const unsigned char* signature) {
	Transaction tx;
	memset(&tx, 0, sizeof(tx));
	memcpy(tx.sender, sender, ADDRESS_SIZE);
	memcpy(tx.receiver, receiver, ADDRESS_SIZE);
	tx.amount = amount;
	memcpy(tx.signature, signature, SIGNATURE_SIZE);

	return verify_transaction_signature(&tx);
}