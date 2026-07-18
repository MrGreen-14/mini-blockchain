#ifndef BLOCKCHAIN_H
#define BLOCKCHAIN_H

#include "block.h"
#include "export.h"
#include <cstddef>

struct Blockchain{
	Block* blocks;
	size_t count;
	size_t capacity;
};

Blockchain create_blockchain();
void free_blockchain(Blockchain* chain);

BLOCKCHAIN_API Blockchain* create_blockchain_heap();
BLOCKCHAIN_API void destroy_blockchain(Blockchain* chain);

BLOCKCHAIN_API Block* begin_block(Blockchain* chain);
BLOCKCHAIN_API int commit_block(Blockchain* chain, int difficulty, volatile int* stop_flag);
BLOCKCHAIN_API int is_chain_valid(const Blockchain* chain);
#endif // !BLOCKCHAIN_H
