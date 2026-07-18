#include "block.h"
#include "blockchain.h"
#include "mining.h"
#include "merkle.h"
#include "transaction.h"
#include "persistence.h"
#include "assert.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>

static void make_tx(Transaction* tx, const char* sender, const char* receiver, uint64_t amount) {
    strncpy(tx->sender, sender, ADDRESS_SIZE - 1);
    tx->sender[ADDRESS_SIZE - 1] = '\0';
    strncpy(tx->receiver, receiver, ADDRESS_SIZE - 1);
    tx->receiver[ADDRESS_SIZE - 1] = '\0';
    tx->amount = amount;
}

void test_merkle_determinism() {
    Transaction txs[2];
    make_tx(&txs[0], "Alice", "Bob", 100);
    make_tx(&txs[1], "Bob", "Carol", 50);

    char root1[65], root2[65];
    compute_merkle_root(txs, 2, root1);
    compute_merkle_root(txs, 2, root2);

    int ok = (strcmp(root1, root2) == 0);
    printf("[%s] test_merkle_determinism\n", ok ? "PASS" : "FAIL");
}

void test_merkle_sensitivity() {
    Transaction txs[2];
    make_tx(&txs[0], "Alice", "Bob", 100);
    make_tx(&txs[1], "Bob", "Carol", 50);

    char root_before[65];
    compute_merkle_root(txs, 2, root_before);

    txs[1].amount = 51;

    char root_after[65];
    compute_merkle_root(txs, 2, root_after);

    int ok = (strcmp(root_before, root_after) != 0);
    printf("[%s] test_merkle_sensitivity (avalanche la nivel de Merkle root)\n", ok ? "PASS" : "FAIL");
}

void test_merkle_odd_count() {
    Transaction txs[3];
    make_tx(&txs[0], "A", "B", 1);
    make_tx(&txs[1], "B", "C", 2);
    make_tx(&txs[2], "C", "D", 3);

    char root[65];
    compute_merkle_root(txs, 3, root);

    int ok = (strlen(root) == 64);
    printf("[%s] test_merkle_odd_count (numar impar, nodul dublat, fara crash)\n", ok ? "PASS" : "FAIL");
}

void test_block_with_transactions() {
    Blockchain chain = create_blockchain();

    Block* b = begin_block(&chain);
    add_transaction_to_block(b, "Alice", "Bob", 500);
    add_transaction_to_block(b, "Bob", "Carol", 200);
    commit_block(&chain, DIFFICULTY,NULL);

    Block* committed = &chain.blocks[0];
    int ok = (strlen(committed->merkle_root) == 64) && (committed->transaction_count == 2);
    printf("[%s] test_block_with_transactions\n", ok ? "PASS" : "FAIL");

    free_blockchain(&chain);
}

void test_chain_valid_with_transactions() {
    Blockchain chain = create_blockchain();

    Block* b1 = begin_block(&chain);
    add_transaction_to_block(b1, "Alice", "Bob", 500);
    commit_block(&chain, DIFFICULTY, NULL);

    Block* b2 = begin_block(&chain);
    add_transaction_to_block(b2, "Bob", "Carol", 200);
    add_transaction_to_block(b2, "Carol", "Dave", 100);
    commit_block(&chain, DIFFICULTY, NULL);

    int valid = is_chain_valid(&chain);
    printf("[%s] test_chain_valid_with_transactions\n", valid ? "PASS" : "FAIL");

    free_blockchain(&chain);
}

void test_transaction_tampering_detected() {
    Blockchain chain = create_blockchain();

    Block* b1 = begin_block(&chain);
    add_transaction_to_block(b1, "Alice", "Bob", 500);
    commit_block(&chain, DIFFICULTY, NULL);

    // Atac simulat: modificam suma DUPA commit, fara sa recalculam merkle root
    chain.blocks[0].transactions[0].amount = 999999;

    int valid = is_chain_valid(&chain);
    printf("[%s] test_transaction_tampering_detected (lant INVALID)\n", !valid ? "PASS" : "FAIL");

    free_blockchain(&chain);
}

void test_save_load_roundtrip(void) {
    Blockchain chain = create_blockchain();

    Block* b1 = begin_block(&chain);
    add_transaction_to_block(b1, "alice", "bob", 100);   // <- string-uri + amount direct, nu &tx1
    commit_block(&chain, DIFFICULTY, NULL);

    Block* b2 = begin_block(&chain);
    add_transaction_to_block(b2, "bob", "carol", 40);    // <- la fel
    commit_block(&chain, DIFFICULTY, NULL);

    int saved = save_chain_to_file(&chain, "test_chain.dat");
    assert(saved);

    Blockchain* loaded = load_chain_from_file("test_chain.dat");
    assert(loaded != NULL);
    assert(loaded->count == chain.count);
    assert(strcmp(loaded->blocks[1].hash, chain.blocks[1].hash) == 0);
    assert(is_chain_valid(loaded));

    free_blockchain(&chain);
    free_blockchain(loaded);
    printf("test_save_load_roundtrip: PASSED\n");
}

void test_load_corrupted_file() {
    FILE* f = fopen("garbage.dat", "wb");
    uint32_t junk = 0xDEADBEEF;
    fwrite(&junk, sizeof(junk), 1, f);
    fclose(f);

    Blockchain* loaded = load_chain_from_file("garbage.dat");
    assert(loaded == NULL);

    remove("garbage.dat");
    printf("test_load_corrupted_file: PASSED\n");
}

void test_load_truncated_file() {
    Blockchain chain = create_blockchain();

    Block* b = begin_block(&chain);
    add_transaction_to_block(b, "x", "y", 1);
    commit_block(&chain, DIFFICULTY, NULL);

    uint8_t* buffer = NULL;
    size_t length = serialize_chain(&chain, &buffer);
    assert(length > 10);

    Blockchain* loaded = deserialize_chain(buffer, length - 10);
    assert(loaded == NULL);

    free(buffer);
    free_blockchain(&chain);
    printf("test_load_truncated_file: PASSED\n");
}


int main() {
    test_save_load_roundtrip();
    //test_load_corrupted_file();
    //test_load_truncated_file();


    Blockchain chain = create_blockchain();
    Block* block = begin_block(&chain);

    add_coinbase_transaction(block, "MinerAddress1", 50);
    add_transaction_to_block(block, "Alice", "Bob", 100);
    add_transaction_to_block(block, "Bob", "Charlie", 40);

    commit_block(&chain, DIFFICULTY, NULL);

    assert(strcmp(chain.blocks[0].transactions[0].sender, "COINBASE") == 0);
    assert(strcmp(chain.blocks[0].transactions[0].receiver, "MinerAddress1") == 0);
    assert(chain.blocks[0].transactions[0].amount == 50);
    assert(chain.blocks[0].transaction_count == 3);

    printf("test_coinbase_transaction: PASSED\n");


    return 0;
}