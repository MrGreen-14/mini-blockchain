#ifndef BLOCK_H
#define BLOCK_H

#include <cstdint>
#include <cstddef>
#include <ctime>

#define HASH_SIZE 65
#define MAX_DATA_SIZE 256

struct Block {
	uint32_t index;
	time_t timestamp;
	char prev_hash[HASH_SIZE];
	char data[MAX_DATA_SIZE];
	uint32_t nonce;
	char hash[HASH_SIZE];
};

Block create_block(uint32_t index, const char* prev_hash, const char* data);
void print_block(const Block* block);
void serialize_block(const Block* block, char* buffer, size_t buffer_size);
void compute_hash(Block* block);
#endif
