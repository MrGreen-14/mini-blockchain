#include "persistence.h"
#include "block.h"
#include "transaction.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

typedef struct {
	uint8_t* data;
	size_t size;
	size_t capapcity;
}ByteBuffer;

static int bb_ensure_capacity(ByteBuffer*bb,size_t additional) {
	if (bb->size + additional <= bb->capapcity) {
		return 1;
	}

	size_t new_capacity = (bb->capapcity == 0) ? 256 : bb->capapcity * 2;
	while (new_capacity < bb->size + additional) {
		new_capacity *= 2;
	}

	uint8_t* new_data = (uint8_t*)realloc(bb->data, new_capacity);
	if (new_data == NULL) {
		return 0;
	}
	bb->data = new_data;
	bb->capapcity = new_capacity;
	return 1;
}

static int bb_write(ByteBuffer* bb, const void* src, size_t n) {
	if (!bb_ensure_capacity(bb, n)) {
		return 0;
	}
	memcpy(bb->data + bb->size, src, n);
	bb->size += n;
	return 1;
}

static int write_u32(ByteBuffer* bb, uint32_t v) { return bb_write(bb, &v, sizeof(v)); }
static int write_u64(ByteBuffer* bb, uint64_t v) { return bb_write(bb, &v, sizeof(v)); }
static int write_fixed(ByteBuffer* bb, const char* field, size_t field_size) {
	return bb_write(bb, field, field_size);
}

typedef struct {
	const uint8_t* data;
	size_t length;
	size_t offset;
}ByteReader;

static int reader_read(ByteReader* r, void* dst, size_t n) {
	if (r->offset + n > r->length) {
		return 0;
	}
	memcpy(dst, r->data + r->offset, n);
	r->offset += n;
	return 1;
}

static int read_u32(ByteReader* r, uint32_t* out) { return reader_read(r, out, sizeof(*out)); }
static int read_u64(ByteReader* r, uint64_t* out) { return reader_read(r, out, sizeof(*out)); }
static int read_fixed(ByteReader* r, char* dst, size_t field_size) {
	return reader_read(r, dst, field_size);
}

static int append_transaction_raw(Block* block, const Transaction* tx) {
	if (block->transaction_count == block->transaction_capacity) {
		size_t new_capacity = (block->transaction_capacity==0)?4: block->transaction_capacity * 2;
		Transaction* new_arr = (Transaction*)realloc(block->transactions, new_capacity * sizeof(Transaction));
		if (new_arr == NULL) {
			return 0;
		}
		block->transactions = new_arr;
		block->transaction_capacity = new_capacity;
	}
	block->transactions[block->transaction_count] = *tx;
	block->transaction_count++;
	return 1;
}

static int append_block_raw(Blockchain* chain, const Block* block) {
	if (chain->count == chain->capacity) {
		size_t new_capacity = (chain->capacity == 0) ? 4 : chain->capacity * 2;
		Block* new_arr = (Block*)realloc(chain->blocks, new_capacity * sizeof(Block));
		if (new_arr == NULL)return 0;

		chain->blocks = new_arr;
		chain->capacity = new_capacity;
	}
	chain->blocks[chain->count] = *block;
	chain->count++;
	return 1;
}

/*
[MAGIC:4][VERSION:4][BLOCK_COUNT:8]
[idx:4][timestamp:8][prev_hash:65][merkle_root:65][nonce:4][hash:65][tx_count:8]
  [sender:65][receiver:65][amount:8][signature:64] <- tranzactia 0 a blocului 0
  [sender:65][receiver:65][amount:8][signature:64] <- tranzactia 1 a blocului 0
  ...
[idx:4][timestamp:8][prev_hash:65]...<- blocul 1 incepe aici
...
*/

size_t serialize_chain(const Blockchain* chain, uint8_t** out_buffer) {
	if (chain == NULL || out_buffer == NULL) {
		return 0;
	}

	ByteBuffer bb = { NULL,0,0 };
	if (!write_u32(&bb, BLOCKCHAIN_MAGIC)) goto fail;
	if (!write_u32(&bb, BLOCKCHAIN_VERSION)) goto fail;
	if (!write_u64(&bb, (uint64_t)chain->count)) goto fail;

	for (size_t i = 0; i < chain->count; i++){
		const Block* b = &chain->blocks[i];

		if (!write_u32(&bb, b->index)) goto fail;
		if(!write_u64(&bb,(uint64_t)b->timestamp))goto fail; //time_t->uint64_t
		if(!write_fixed(&bb,b->prev_hash,HASH_SIZE)) goto fail;
		if (!write_fixed(&bb, b->merkle_root, HASH_SIZE)) goto fail;
		if (!write_u32(&bb, b->nonce)) goto fail;
		if (!write_fixed(&bb, b->hash, HASH_SIZE)) goto fail;

		if (!write_u64(&bb, (uint64_t)b->transaction_count)) goto fail;
		for (size_t t = 0; t < b->transaction_count; t++) {
			const Transaction* tx = &b->transactions[t];
			if (!write_fixed(&bb, tx->sender, ADDRESS_SIZE))   goto fail;
			if (!write_fixed(&bb, tx->receiver, ADDRESS_SIZE)) goto fail;
			if (!write_u64(&bb, tx->amount)) goto fail;
			if (!write_fixed(&bb, (const char*)tx->signature, SIGNATURE_SIZE)) goto fail;
		}
	}

	*out_buffer = bb.data;
	return bb.size;

fail:
	free(bb.data);
	*out_buffer = NULL;
	return 0;
}

Blockchain* deserialize_chain(const uint8_t* buffer, size_t length) {
	if (buffer == NULL) {
		return NULL;
	}

	ByteReader r = { buffer, length, 0 };

	uint32_t magic, version;
	uint64_t block_count;

	if (!read_u32(&r, &magic) || magic != BLOCKCHAIN_MAGIC) {
		return NULL;
	}
	if (!read_u32(&r, &version) || version != BLOCKCHAIN_VERSION) {
		return NULL;
	}
	if (!read_u64(&r, &block_count)) {
		return NULL;
	}

	
	Blockchain* chain = (Blockchain*)malloc(sizeof(Blockchain));
	if (chain == NULL) {
		return NULL;
	}
	*chain = create_blockchain();

	for (uint64_t i = 0; i < block_count; i++) {
		Block block;
		memset(&block, 0, sizeof(block));

		uint64_t raw_timestamp, tx_count;

		if (!read_u32(&r, &block.index)) goto fail;
		if (!read_u64(&r, &raw_timestamp)) goto fail;
		block.timestamp = (time_t)raw_timestamp;
		if (!read_fixed(&r, block.prev_hash, HASH_SIZE)) goto fail;
		if (!read_fixed(&r, block.merkle_root, HASH_SIZE)) goto fail;
		if (!read_u32(&r, &block.nonce)) goto fail;
		if (!read_fixed(&r, block.hash, HASH_SIZE)) goto fail;

		if (!read_u64(&r, &tx_count)) goto fail;

		block.transactions = NULL;
		block.transaction_count = 0;
		block.transaction_capacity = 0;

		for (uint64_t t = 0; t < tx_count; t++) {
			Transaction tx;
			if (!read_fixed(&r, tx.sender, ADDRESS_SIZE)) goto fail;
			if (!read_fixed(&r, tx.receiver, ADDRESS_SIZE)) goto fail;
			if (!read_u64(&r, &tx.amount)) goto fail;
			if (!read_fixed(&r, (char*)tx.signature, SIGNATURE_SIZE)) goto fail;
			if (!append_transaction_raw(&block, &tx)) goto fail;
		}

		if (!append_block_raw(chain, &block)) {
			free(block.transactions);
			goto fail;
		}
	}

	return chain;

fail:
	free_blockchain(chain);  
	free(chain);             
	return NULL;
}

int save_chain_to_file(const Blockchain* chain, const char* filepath) {
	uint8_t* buffer = NULL;
	size_t length = serialize_chain(chain, &buffer);
	if (length == 0) {
		return 0;
	}

	FILE* f = fopen(filepath, "wb");
	if (f == NULL) {
		free(buffer);
		return 0;
	}

	size_t written = fwrite(buffer, 1, length, f);
	fclose(f);
	free(buffer);

	return written == length;
}

Blockchain* load_chain_from_file(const char* filepath) {
	FILE* f = fopen(filepath, "rb");
	if (!f)
		return NULL;

	fseek(f, 0, SEEK_END);
	long file_size = ftell(f);
	fseek(f, 0, SEEK_SET);

	if (file_size <= 0) {
		fclose(f);
		return NULL;
	}

	uint8_t* buffer = (uint8_t*)malloc((size_t)file_size);
	if (buffer == NULL) {
		fclose(f);
		return NULL;
	}

	size_t read_bytes = fread(buffer, 1, (size_t)file_size, f);
	fclose(f);

	if (read_bytes != (size_t)file_size) {
		free(buffer);
		return NULL;
	}
	Blockchain* chain = deserialize_chain(buffer, read_bytes);
	free(buffer);
	return chain;
}

void free_serialized_buffer(uint8_t* buffer) {
	free(buffer);
}