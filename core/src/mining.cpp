#include "mining.h"
#include <cstdio>
#include <ctime>

static int hash_meets_difficulty(const char* hash, int difficulty) {
	for (int i = 0; i < difficulty; i++){
		if (hash[i] != '0') {
			return 0;
		}
	}
	return 1;
}

int mine_block(Block* block, int difficulty, volatile int* stop_flag) {
	clock_t start = clock();
	block->nonce = 0;
	compute_hash(block);

	while (!hash_meets_difficulty(block->hash, difficulty)) {
		if (stop_flag != NULL && *stop_flag) {
			printf("Bloc #%u: minare intrerupta la nonce=%u\n", block->index, block->nonce);
			return 0;
		}
		block->nonce++;
		compute_hash(block);
	}

	clock_t end=clock();
	double seconds = (double)(end - start) / CLOCKS_PER_SEC;

	printf("Bloc #%u minat: nonce=%u, timp=%.4f sec\n", block->index, block->nonce, seconds);
	return 1;
}