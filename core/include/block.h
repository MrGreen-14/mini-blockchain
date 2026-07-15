#ifndef BLOCK_H
#define BLOCK_H

#include <cstdint>
#include <cstddef>
#include <ctime>
#include "transaction.h"

#define HASH_SIZE 65

struct Block {
	uint32_t index;
	time_t timestamp;
	char prev_hash[HASH_SIZE];
	Transaction* transactions;
	size_t transaction_count;
	size_t transaction_capacity;
	char merkle_root[HASH_SIZE];
	uint32_t nonce;
	char hash[HASH_SIZE];
};

Block create_block(uint32_t index, const char* prev_hash);
void add_transaction_to_block(Block* block, const char* sender, const char* receiver, uint64_t amount);
void finalize_merkle_root(Block* block);

void free_block(Block* block);
void print_block(const Block* block);
void serialize_block(const Block* block, char* buffer, size_t buffer_size);
void compute_hash(Block* block);
#endif
