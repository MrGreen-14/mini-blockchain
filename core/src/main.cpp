#include "block.h"
#include "blockchain.h"
#include "mining.h"
#include <cstdio>
#include <cstring>

void test_create_block() {
    Block b = create_block(0, "0000000000000000000000000000000000000000000000000000000000000",
        "Genesis Block");

    int ok = (b.index == 0) && (strcmp(b.data, "Genesis Block") == 0) && (b.nonce == 0);
    printf("[%s] test_create_block\n", ok ? "PASS" : "FAIL");
}

void test_serialize_sensitivity() {
    Block b1 = create_block(1, "abc", "Hello");
    Block b2 = create_block(1, "abc", "Hell0");

    char buf1[512], buf2[512];
    serialize_block(&b1, buf1, sizeof(buf1));
    serialize_block(&b2, buf2, sizeof(buf2));

   
    int ok = (strcmp(buf1, buf2) != 0);
    printf("[%s] test_serialize_sensitivity\n", ok ? "PASS" : "FAIL");
}

void test_mining_produces_valid_hash() {
    Blockchain chain = create_blockchain();
    add_block(&chain, "bloc de test pentru mining");

    const char* hash = chain.blocks[chain.count - 1].hash;
    int ok = 1;
    for (int i = 0; i < DIFFICULTY; i++) {
        if (hash[i] != '0') {
            ok = 0;
            break;
        }
    }

    printf("[%s] test_mining_produces_valid_hash (hash-ul incepe cu %d zerouri)\n",
        ok ? "PASS" : "FAIL", DIFFICULTY);

    free_blockchain(&chain);
}

void test_chain_still_valid_with_mining() {
    Blockchain chain = create_blockchain();
    add_block(&chain, "primul bloc");
    add_block(&chain, "al doilea bloc");
    add_block(&chain, "al treilea bloc");

    int valid = is_chain_valid(&chain);
    printf("[%s] test_chain_still_valid_with_mining\n", valid ? "PASS" : "FAIL");

    free_blockchain(&chain);
}

void test_mining_difficulty_timing() {
    Block block1 = create_block(0, "0000000000000000000000000000000000000000000000000000000000000", "test dificultate");
    mine_block(&block1, 3);

    Block block2 = create_block(0, "0000000000000000000000000000000000000000000000000000000000000", "test dificultate");
    mine_block(&block2, 5);

    printf("Comparatie: dificultate 3 vs dificultate 5 (vezi timpii si nonce-urile afisate mai sus)\n");
}

int main() {

    //test_mining_produces_valid_hash();
    test_chain_still_valid_with_mining();
    //test_mining_difficulty_timing();
    return 0;
}