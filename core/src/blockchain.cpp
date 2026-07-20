#include "blockchain.h"
#include "mining.h"
#include "merkle.h"
#include <cstdlib>
#include <cstring>
#include <cstdio>

#define INITIAL_CAPACITY 4

Blockchain create_blockchain() {
	Blockchain chain;
	chain.capacity = INITIAL_CAPACITY;

	chain.blocks = (Block*)malloc(INITIAL_CAPACITY * sizeof(Block));
	if (!chain.blocks) { exit(1); }

	memset(chain.blocks, 0, chain.capacity * sizeof(Block));
	chain.count = 0;
	return chain;
}

void free_blockchain(Blockchain* chain) {
	for (size_t i = 0; i < chain->count; i++){
		free_block(&chain->blocks[i]);
	}
	free(chain->blocks);
	chain->blocks = NULL;
	chain->count = 0;
	chain->capacity = 0;
}

Block* begin_block(Blockchain* chain) {
	if (chain->count == chain->capacity) {
		chain->capacity *= 2;
		Block* new_array = (Block*)realloc(chain->blocks, chain->capacity * sizeof(Block));
		if (!new_array)exit(1);
		chain->blocks = new_array;
	}

	// daca slotul a fost deja folosit intr-o incercare de minare anterioara,
	// intrerupta inainte sa comita, elibereaza array-ul vechi de tranzactii
	// inainte sa il suprascriem -- altfel pierdem pointer-ul si memoria ramane blocata
	if (chain->blocks[chain->count].transactions != NULL) {
		free(chain->blocks[chain->count].transactions);
	}

	const char* prev_hash;
	uint32_t new_index;

	if (chain->count == 0) {
		prev_hash = "0000000000000000000000000000000000000000000000000000000000000";
		new_index = 0;
	}
	else {
		prev_hash = chain->blocks[chain->count - 1].hash;
		new_index = chain->blocks[chain->count - 1].index + 1;
	}

	chain->blocks[chain->count] = create_block(new_index, prev_hash);
	return &chain->blocks[chain->count];
}

int commit_block(Blockchain* chain, int difficulty, volatile int* stop_flag) {
	Block* block = &chain->blocks[chain->count];
	finalize_merkle_root(block);

	int success = mine_block(block, difficulty, stop_flag);
	if (success) {
		chain->count++;
	}
	return success;
}

int is_chain_valid(const Blockchain* chain) {
	for (size_t i = 0; i < chain->count; i++){
		const Block* block = &chain->blocks[i]; //shallow copy

		char recalculated_merkle[65];
		compute_merkle_root(block->transactions, block->transaction_count, recalculated_merkle);

		if (strcmp(recalculated_merkle, block->merkle_root) != 0) {
			printf("Bloc #%u: merkle root invalid (tranzactiile au fost modificate)\n", block->index);
			return 0;
		}

		Block temp = *block;
		char stored_hash[65];
		strncpy(stored_hash, temp.hash, 65);
		stored_hash[64] = '\0';

		compute_hash(&temp);
		if (strcmp(temp.hash, stored_hash) != 0) {
			printf("Bloc #%u: integritate invalida (hash nu corespunde continutului)\n", block->index);
			return 0;
		}

		if (i > 0) {
			const char* expected_prev_hash = chain->blocks[i - 1].hash;
			if (strcmp(block->prev_hash, expected_prev_hash) != 0) {
				printf("Bloc #%u: prev_hash nu corespunde cu hash-ul blocului anterior\n", block->index);
				return 0;
			}
		}
	}
	return 1;
}

Blockchain* create_blockchain_heap() {
	Blockchain* chain = (Blockchain*)malloc(sizeof(Blockchain));
	if (!chain) return NULL;
	*chain = create_blockchain();
	return chain;
}

void destroy_blockchain(Blockchain* chain) {
	if (!chain) return;
	free_blockchain(chain);
	free(chain);
}

size_t get_chain_length(const Blockchain* chain) {
	if (!chain) return 0;
	return chain->count;
}