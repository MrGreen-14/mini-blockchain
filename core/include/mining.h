#ifndef MINING_H
#define MINING_H

#include "block.h"
#include "export.h"

#define DIFFICULTY 4

BLOCKCHAIN_API int mine_block(Block* block, int difficulty, volatile int* stop_flag);

#endif // !MINING_H
