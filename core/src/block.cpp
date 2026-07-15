#include "block.h"
#include "sha256.h"
#include "merkle.h"
#include <cstdio>
#include <cstring>
#include <cstdlib>

#define INITIAL_TX_CAPACITY 4


Block create_block(uint32_t index, const char* prev_hash) {
	Block block;
	memset(&block, 0, sizeof(Block));

	block.index = index;
	block.timestamp = time(NULL);

	strncpy(block.prev_hash, prev_hash, HASH_SIZE - 1);
	block.prev_hash[HASH_SIZE - 1] = '\0';

	block.transactions = NULL;
	block.transaction_count = 0;
	block.transaction_capacity = 0;

	block.nonce = 0;
	compute_hash(&block);

	return block;
}

void add_transaction_to_block(Block* block, const char* sender, const char* receiver, uint64_t amount) {
	if (block->transaction_count == block->transaction_capacity) {
		size_t new_capacity = (block->transaction_capacity == 0) ? 
			INITIAL_TX_CAPACITY : block->transaction_capacity * 2;

		Transaction* new_array = (Transaction*)realloc(block->transactions, new_capacity * sizeof(Transaction));
		if (!new_array)exit(1);

		block->transactions = new_array;
		block->transaction_capacity = new_capacity;
	}

	Transaction* tx = &block->transactions[block->transaction_count];

	strncpy(tx->sender, sender, ADDRESS_SIZE - 1);
	tx->sender[ADDRESS_SIZE - 1] = '\0';

	strncpy(tx->receiver, receiver, ADDRESS_SIZE - 1);
	tx->receiver[ADDRESS_SIZE - 1] = '\0';

	tx->amount = amount;

	block->transaction_count++;
}

void finalize_merkle_root(Block* block) {
	compute_merkle_root(block->transactions, block->transaction_count, block->merkle_root);
}

void free_block(Block* block) {
	free(block->transactions);
	block->transactions = NULL;
	block->transaction_count = 0;
	block->transaction_capacity = 0;
}

void print_block(const Block* block) {
	printf("Block #%u\n", block->index);
	printf("  Timestamp: %ld\n", (long)block->timestamp);
	printf("  Prev hash: %s\n", block->prev_hash);
	printf("  Transactions: %zu\n", block->transaction_count);
	for (size_t i = 0; i < block->transaction_count; i++){
		printf("    [%zu] %s -> %s : %llu\n", i,
			block->transactions[i].sender,
			block->transactions[i].receiver,
			(unsigned long long)block->transactions[i].amount);
	}
	printf("  Merkle root: %s\n", block->merkle_root);
	printf("  Nonce:     %u\n", block->nonce);
	printf("  Hash:      %s\n", block->hash);
}

void serialize_block(const Block* block, char* buffer, size_t buffer_size) {
	snprintf(buffer, buffer_size, "%u%ld%s%s%u", 
		block->index, (long)block->timestamp, 
		block->prev_hash, block->merkle_root, 
		block->nonce);
}

void compute_hash(Block*block) {
	char serialized[512];
	serialize_block(block, serialized, sizeof(serialized));

	compute_sha256_hex((const unsigned char*)serialized, strlen(serialized), block->hash);
}