#include "block.h"
#include "blockchain.h"
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

void test_blockchain_valid() {
    Blockchain chain = create_blockchain();
    add_block(&chain, "primul bloc");
    add_block(&chain, "al doilea bloc");
    add_block(&chain, "al treilea bloc");

    int valid = is_chain_valid(&chain);
    printf("[%s] test_blockchain_valid\n", valid ? "PASS" : "FAIL");

    free_blockchain(&chain);
}

void test_tampering_detected() {
    Blockchain chain = create_blockchain();
    add_block(&chain, "bloc original");
    add_block(&chain, "bloc doi");
    add_block(&chain, "bloc trei");

    strncpy(chain.blocks[1].data, "date falsificate", MAX_DATA_SIZE - 1);

    int valid = is_chain_valid(&chain);
    printf("[%s] test_tampering_detected (asteptam lant INVALID)\n", !valid ? "PASS" : "FAIL");

    free_blockchain(&chain);

}

int main() {

    test_tampering_detected();

    return 0;
}