//#include <openssl/sha.h>
//#include <cstdio>
//
//int main() {
//    unsigned char hash[SHA256_DIGEST_LENGTH];
//    const char* data = "test";
//    SHA256((unsigned char*)data, 4, hash);
//
//    for (int i = 0; i < SHA256_DIGEST_LENGTH; i++)
//        printf("%02x", hash[i]);
//    printf("\n");
//    return 0;
//}

#include "block.h"
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

int main() {

    test_create_block();
    test_serialize_sensitivity();

    printf("\n=== Exemplu vizual ===\n");
    Block genesis = create_block(0, "0000000000000000000000000000000000000000000000000000000000000",
        "Genesis Block");
    print_block(&genesis);

    char buffer[512];
    serialize_block(&genesis, buffer, sizeof(buffer));
    printf("\nSerializare: %s\n", buffer);

    return 0;
}