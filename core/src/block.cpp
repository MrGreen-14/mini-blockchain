#include "block.h"
#include "sha256.h"
#include <cstdio>
#include <cstring>

Block create_block(uint32_t index, const char* prev_hash, const char* data) {
	Block block;
	memset(&block, 0, sizeof(Block));

	block.index = index;
	block.timestamp = time(NULL);

	strncpy(block.prev_hash, prev_hash, HASH_SIZE - 1);
	block.prev_hash[HASH_SIZE - 1] = '\0';

	strncpy(block.data, data, MAX_DATA_SIZE - 1);
	block.data[MAX_DATA_SIZE - 1] = '\0';

	block.nonce = 0;
	compute_hash(&block);

	return block;
	//b1 1784010376
}

void print_block(const Block* block) {
	printf("Block #%u\n", block->index);
	printf("  Timestamp: %ld\n", (long)block->timestamp);
	printf("  Prev hash: %s\n", block->prev_hash);
	printf("  Data:      %s\n", block->data);
	printf("  Nonce:     %u\n", block->nonce);
	printf("  Hash:      %s\n", block->hash);
}

void serialize_block(const Block* block, char* buffer, size_t buffer_size) {
	snprintf(buffer, buffer_size, "%u%ld%s%s%u", 
		block->index, (long)block->timestamp, 
		block->prev_hash, block->data, 
		block->nonce);
}

void compute_hash(Block*block) {
	char serialized[512];
	serialize_block(block, serialized, sizeof(serialized));

	compute_sha256_hex((const unsigned char*)serialized, strlen(serialized), block->hash);
}