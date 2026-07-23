#ifndef PERSISTENCE
#define PERSISTENCE

#include <stdint.h>
#include <stddef.h>
#include "blockchain.h"
#include "export.h"

#define BLOCKCHAIN_MAGIC   0x424C4B43u  /* "BLKC" -- identifica fisierul ca fiind al nostru */
#define BLOCKCHAIN_VERSION 1u           // v2: transaction are acum campul signature (Modulul 9)

BLOCKCHAIN_API size_t serialize_chain(const Blockchain*chain,uint8_t**out_buffer);
BLOCKCHAIN_API Blockchain* deserialize_chain(const uint8_t* buffer, size_t lenght);
BLOCKCHAIN_API void free_serialized_buffer(uint8_t* buffer);

int save_chain_to_file(const Blockchain* chain, const char* filepath);
Blockchain* load_chain_from_file(const char* filepath);

#endif // !PERSISTENCE
