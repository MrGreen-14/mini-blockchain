#ifndef PERSISTENCE
#define PERSISTENCE

#include <stdint.h>
#include <stddef.h>
#include "blockchain.h"

#define BLOCKCHAIN_MAGIC   0x424C4B43u  /* "BLKC" -- identifica fisierul ca fiind al nostru */
#define BLOCKCHAIN_VERSION 1u           /* incrementat daca schimbam vreodata layout-ul */

size_t serialize_chain(const Blockchain*chain,uint8_t**out_buffer);

Blockchain* deserialize_chain(const uint8_t* buffer, size_t lenght);

int save_chain_to_file(const Blockchain* chain, const char* filepath);
Blockchain* load_chain_from_file(const char* filepath);

#endif // !PERSISTENCE
