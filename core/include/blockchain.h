#ifndef BLOCKCHAIN_H
#define BLOCKCHAIN_H

#include "block.h"
#include <cstddef>

struct Blockchain{
	Block* blocks;
	size_t count;
	size_t capacity;
};

Blockchain create_blockchain();
void free_blockchain(Blockchain* chain);
void add_block(Blockchain* chain, const char* data);
int is_chain_valid(const Blockchain* chain);

#endif // !BLOCKCHAIN_H
