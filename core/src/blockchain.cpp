#include "blockchain.h"
#include <cstdlib>
#include <cstring>
#include <cstdio>

#define INITIAL_CAPACITY 4

Blockchain create_blockchain() {
	Blockchain chain;
	chain.blocks = (Block*)malloc(INITIAL_CAPACITY * sizeof(Block));
	if (!chain.blocks) { exit(1); }
	chain.count = 0;
	chain.capacity = INITIAL_CAPACITY;
	return chain;
}

void free_blockchain(Blockchain* chain) {
	free(chain->blocks);
	chain->blocks = NULL;
	chain->blocks = 0;
	chain->count = 0;
}

void add_block(Blockchain* chain,const char*data) {
	if (chain->count == chain->capacity) {
		chain->capacity *= 2;
		chain->blocks = (Block*)realloc(chain->blocks, chain->capacity * sizeof(Block));
		if (!chain->blocks)exit(1);
	}

	const char* prev_hash;
	uint32_t new_index;

	if (chain->count == 0) {
		prev_hash = "0000000000000000000000000000000000000000000000000000000000000";
		new_index = 0;
	}
	else {
		prev_hash = chain->blocks[chain->count - 1].hash;
		new_index = chain->blocks[chain->count - 1].index;
	}
	chain->blocks[chain->count] = create_block(new_index, prev_hash, data);
	chain->count++;
}

int is_chain_valid(const Blockchain* chain) {
	for (int i = 0; i < chain->count; i++){
		Block current = chain->blocks[i];
		char recalculated_hash[HASH_SIZE];
		strncpy(recalculated_hash, current.hash, HASH_SIZE);
		recalculated_hash[HASH_SIZE - 1] = '\0';

		compute_hash(&current);
		if (strcmp(current.hash, recalculated_hash) != 0) {
			printf("Bloc #%u: integritate invalida (hash nu corespunde continutului)\n", chain->blocks[i].index);
			return 0;
		}

		if (i > 0) {
			const char* expected_prev_hash = chain->blocks[i - 1].hash;
			if (strcmp(chain->blocks[i].prev_hash, expected_prev_hash) != 0) {
				printf("Bloc #%u: prev_hash nu corespunde cu hash-ul blocului anterior\n", chain->blocks[i].index);
				return 0;
			}
		}
	}
	return 1;
}