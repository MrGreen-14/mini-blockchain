#include "blockchain.h"
#include "block.h"
#include "mining.h"
#include "merkle.h"
#include "transaction.h"
#include "persistence.h"
#include "wallet.h"
#include "sha256.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>


#define TEST_DIFFICULTY 2

//  1. Portofel: generare chei, semnare, verificare, detectie alterare
static int test_wallet_sign_verify() {
    unsigned char priv[PRIVATE_KEY_SIZE], pub[PUBLIC_KEY_SIZE];
    if (!generate_keypair(priv, pub)) {
        printf("[FAIL] test_wallet_sign_verify -- generate_keypair esuat\n");
        return 0;
    }

   
    unsigned char hash[32];
    memset(hash, 0, 32);
    compute_sha256_raw((const unsigned char*)"test data", 9, hash);

    unsigned char sig[SIGNATURE_SIZE];
    if (!sign_hash(priv, hash, sig)) {
        printf("[FAIL] test_wallet_sign_verify -- sign_hash esuat\n");
        return 0;
    }

    // verificarea cu cheia publica corecta trebuie sa treaca
    if (!verify_hash_signature(pub, hash, sig)) {
        printf("[FAIL] test_wallet_sign_verify -- semnatura valida respinsa\n");
        return 0;
    }

    // alteram un byte din hash -- verificarea trebuie sa esueze
    hash[0] ^= 0xFF;
    if (verify_hash_signature(pub, hash, sig)) {
        printf("[FAIL] test_wallet_sign_verify -- semnatura invalida acceptata dupa alterare hash\n");
        return 0;
    }

    // alteram un byte din semnatura (cu hash-ul original) -- la fel, trebuie sa esueze
    hash[0] ^= 0xFF; // revenim la hash initial
    sig[0] ^= 0xFF;
    if (verify_hash_signature(pub, hash, sig)) {
        printf("[FAIL] test_wallet_sign_verify -- semnatura alterata acceptata\n");
        return 0;
    }

    printf("[PASS] test_wallet_sign_verify\n");
    return 1;
}


//  2. Pipeline complet: chei -> tranzactie semnata + coinbase -> minare ->  lant valid   
static int test_signed_chain_pipeline() {
    // generam doua perechi de chei (expeditor + destinatar)
    unsigned char priv_a[PRIVATE_KEY_SIZE], pub_a[PUBLIC_KEY_SIZE];
    unsigned char priv_b[PRIVATE_KEY_SIZE], pub_b[PUBLIC_KEY_SIZE];
    generate_keypair(priv_a, pub_a);
    generate_keypair(priv_b, pub_b);

    // semnam o tranzactie: A -> B, 100 unitati
    unsigned char sig[SIGNATURE_SIZE];
    if (!sign_transaction_raw((const char*)pub_a, (const char*)pub_b, 100, priv_a, sig)) {
        printf("[FAIL] test_signed_chain_pipeline -- sign_transaction_raw esuat\n");
        return 0;
    }

    // verificam semnatura inainte de a o pune in bloc
    if (!verify_transaction_signature_raw((const char*)pub_a, (const char*)pub_b, 100, sig)) {
        printf("[FAIL] test_signed_chain_pipeline -- verify esuat pe semnatura proaspata\n");
        return 0;
    }

    // construim un lant cu un singur bloc: coinbase + tranzactia semnata
    Blockchain chain = create_blockchain();
    Block* b = begin_block(&chain);
    add_coinbase_transaction(b, "Miner-Test", 50);
    add_transaction_to_block(b, (const char*)pub_a, (const char*)pub_b, 100, sig);
    commit_block(&chain, TEST_DIFFICULTY, NULL);

    int valid = is_chain_valid(&chain);
    free_blockchain(&chain);

    if (!valid) {
        printf("[FAIL] test_signed_chain_pipeline -- lantul nu trece is_chain_valid\n");
        return 0;
    }

    printf("[PASS] test_signed_chain_pipeline\n");
    return 1;
}

//3. Persistenta: serializare -> deserializare -> lantul restaurat e valid

static int test_persistence_roundtrip() {
    unsigned char priv_a[PRIVATE_KEY_SIZE], pub_a[PUBLIC_KEY_SIZE];
    unsigned char priv_b[PRIVATE_KEY_SIZE], pub_b[PUBLIC_KEY_SIZE];
    generate_keypair(priv_a, pub_a);
    generate_keypair(priv_b, pub_b);

    unsigned char sig[SIGNATURE_SIZE];
    sign_transaction_raw((const char*)pub_a, (const char*)pub_b, 200, priv_a, sig);

    // lant cu 2 blocuri (fiecare cu coinbase + o tranzactie semnata)
    Blockchain chain = create_blockchain();

    Block* b1 = begin_block(&chain);
    add_coinbase_transaction(b1, "Miner-Test", 50);
    add_transaction_to_block(b1, (const char*)pub_a, (const char*)pub_b, 200, sig);
    commit_block(&chain, TEST_DIFFICULTY, NULL);

    // al doilea bloc: B -> A (semnatura noua, cu cheia privata a lui B)
    unsigned char sig2[SIGNATURE_SIZE];
    sign_transaction_raw((const char*)pub_b, (const char*)pub_a, 75, priv_b, sig2);

    Block* b2 = begin_block(&chain);
    add_coinbase_transaction(b2, "Miner-Test", 50);
    add_transaction_to_block(b2, (const char*)pub_b, (const char*)pub_a, 75, sig2);
    commit_block(&chain, TEST_DIFFICULTY, NULL);

    // serializare in buffer
    uint8_t* buffer = NULL;
    size_t buf_len = serialize_chain(&chain, &buffer);
    if (buf_len == 0 || buffer == NULL) {
        printf("[FAIL] test_persistence_roundtrip -- serialize_chain a returnat 0\n");
        free_blockchain(&chain);
        return 0;
    }

    // deserializare din buffer
    Blockchain* loaded = deserialize_chain(buffer, buf_len);
    free(buffer);

    if (loaded == NULL) {
        printf("[FAIL] test_persistence_roundtrip -- deserialize_chain a returnat NULL\n");
        free_blockchain(&chain);
        return 0;
    }

    // verificari: acelasi numar de blocuri, acelasi hash pe ultimul bloc, lant valid
    int ok = 1;
    if (loaded->count != chain.count) {
        printf("[FAIL] test_persistence_roundtrip -- count difera: %zu vs %zu\n", loaded->count, chain.count);
        ok = 0;
    }
    if (ok && strcmp(loaded->blocks[1].hash, chain.blocks[1].hash) != 0) {
        printf("[FAIL] test_persistence_roundtrip -- hash-ul blocului 1 difera\n");
        ok = 0;
    }
    if (ok && !is_chain_valid(loaded)) {
        printf("[FAIL] test_persistence_roundtrip -- lantul restaurat nu trece is_chain_valid\n");
        ok = 0;
    }

    free_blockchain(&chain);
    free_blockchain(loaded);
    free(loaded);

    if (ok) printf("[PASS] test_persistence_roundtrip\n");
    return ok;
}

//  4. Tamper detection: modificam suma dupa minare -> lant invalid

static int test_tamper_after_mining() {
    unsigned char priv[PRIVATE_KEY_SIZE], pub[PUBLIC_KEY_SIZE];
    unsigned char priv_r[PRIVATE_KEY_SIZE], pub_r[PUBLIC_KEY_SIZE];
    generate_keypair(priv, pub);
    generate_keypair(priv_r, pub_r);

    unsigned char sig[SIGNATURE_SIZE];
    sign_transaction_raw((const char*)pub, (const char*)pub_r, 500, priv, sig);

    Blockchain chain = create_blockchain();
    Block* b = begin_block(&chain);
    add_coinbase_transaction(b, "Miner-Test", 50);
    add_transaction_to_block(b, (const char*)pub, (const char*)pub_r, 500, sig);
    commit_block(&chain, TEST_DIFFICULTY, NULL);

    // lantul trebuie sa fie valid INAINTE de alterare
    if (!is_chain_valid(&chain)) {
        printf("[FAIL] test_tamper_after_mining -- lantul nu e valid nici inainte de alterare\n");
        free_blockchain(&chain);
        return 0;
    }

    // atac simulat: un atacator modifica suma tranzactiei dupa minare,
    // fara sa recalculeze merkle root sau hash-ul blocului
    // (tranzactia 0 e coinbase, tranzactia 1 e cea semnata)
    chain.blocks[0].transactions[1].amount = 999999;

    int still_valid = is_chain_valid(&chain);
    free_blockchain(&chain);

    if (still_valid) {
        printf("[FAIL] test_tamper_after_mining -- lantul e inca 'valid' dupa alterare!\n");
        return 0;
    }

    printf("[PASS] test_tamper_after_mining\n");
    return 1;
}

//  5. Input corupt: magic gresit + buffer trunchiat -> NULL, fara crash

static int test_corrupted_input() {
    //fisier cu magic gresit
    const char* garbage_path = "test_garbage.dat";
    FILE* f = fopen(garbage_path, "wb");
    uint32_t junk = 0xDEADBEEF;
    fwrite(&junk, sizeof(junk), 1, f);
    fclose(f);

    Blockchain* loaded = load_chain_from_file(garbage_path);
    remove(garbage_path);
    if (loaded != NULL) {
        printf("[FAIL] test_corrupted_input -- fisier cu magic gresit acceptat\n");
        destroy_blockchain(loaded);
        return 0;
    }

    //buffer trunchiat: serializare valida, apoi trunchiata cu 10 bytes
    unsigned char priv[PRIVATE_KEY_SIZE], pub[PUBLIC_KEY_SIZE];
    unsigned char priv_r[PRIVATE_KEY_SIZE], pub_r[PUBLIC_KEY_SIZE];
    generate_keypair(priv, pub);
    generate_keypair(priv_r, pub_r);

    unsigned char sig[SIGNATURE_SIZE];
    sign_transaction_raw((const char*)pub, (const char*)pub_r, 1, priv, sig);

    Blockchain chain = create_blockchain();
    Block* b = begin_block(&chain);
    add_coinbase_transaction(b, "M", 50);
    add_transaction_to_block(b, (const char*)pub, (const char*)pub_r, 1, sig);
    commit_block(&chain, TEST_DIFFICULTY, NULL);

    uint8_t* buffer = NULL;
    size_t buf_len = serialize_chain(&chain, &buffer);
    free_blockchain(&chain);

    if (buf_len < 10) {
        printf("[FAIL] test_corrupted_input -- buffer prea scurt pentru test\n");
        free(buffer);
        return 0;
    }

    Blockchain* truncated = deserialize_chain(buffer, buf_len - 10);
    free(buffer);

    if (truncated != NULL) {
        printf("[FAIL] test_corrupted_input -- buffer trunchiat acceptat\n");
        free_blockchain(truncated);
        free(truncated);
        return 0;
    }

    printf("[PASS] test_corrupted_input\n");
    return 1;
}


//  6. Capacity boundary: mineaza 5 blocuri (peste INITIAL_CAPACITY=4)
// forteaza realloc-ul din begin_block() si confirma ca nu mai crapa.
static int test_capacity_growth() {
    unsigned char priv[PRIVATE_KEY_SIZE], pub[PUBLIC_KEY_SIZE];
    unsigned char priv_r[PRIVATE_KEY_SIZE], pub_r[PUBLIC_KEY_SIZE];
    generate_keypair(priv, pub);
    generate_keypair(priv_r, pub_r);

    Blockchain chain = create_blockchain();

    for (int i = 0; i < 5; i++) {
        unsigned char sig[SIGNATURE_SIZE];
        sign_transaction_raw((const char*)pub, (const char*)pub_r, 10, priv, sig);

        Block* b = begin_block(&chain);
        add_coinbase_transaction(b, "Miner-Test", 50);
        add_transaction_to_block(b, (const char*)pub, (const char*)pub_r, 10, sig);
        commit_block(&chain, TEST_DIFFICULTY, NULL);
    }

    int ok = (chain.count == 5) && is_chain_valid(&chain);
    free_blockchain(&chain);

    if (!ok) {
        printf("[FAIL] test_capacity_growth -- lant invalid dupa cresterea capacitatii\n");
        return 0;
    }

    printf("[PASS] test_capacity_growth (5 blocuri, capacitate crescuta 4 -> 8)\n");
    return 1;
}

int main() {

    int failed = 0;
    failed += !test_wallet_sign_verify();
    failed += !test_signed_chain_pipeline();
    failed += !test_persistence_roundtrip();
    failed += !test_tamper_after_mining();
    failed += !test_corrupted_input();
    failed += !test_capacity_growth();

    printf("\nRezultat: %d/%d teste trecute\n", 6 - failed, 6);
    return failed;
}