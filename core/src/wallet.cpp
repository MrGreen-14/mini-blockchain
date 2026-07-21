#include "wallet.h"
#include <openssl/evp.h>
#include <openssl/ec.h>
#include <openssl/bn.h>
#include <openssl/obj_mac.h>  // NID_secp256k1
#include <openssl/ecdsa.h>

int generate_keypair(unsigned char* private_key_out, unsigned char* public_key_out) {
	int success = 0;

	// pasul 1: construim un EVP_PKEY care contine doar parametrii curbei (secp256k1)
	EVP_PKEY_CTX* pctx = EVP_PKEY_CTX_new_id(EVP_PKEY_EC, NULL);
	if (!pctx) return 0;

	if (EVP_PKEY_paramgen_init(pctx) <= 0) {
		EVP_PKEY_CTX_free(pctx);
		return 0;
	}
	if (EVP_PKEY_CTX_set_ec_paramgen_curve_nid(pctx, NID_secp256k1) <= 0) {
		EVP_PKEY_CTX_free(pctx);
		return 0;
	}

	EVP_PKEY* params = NULL;
	if (EVP_PKEY_paramgen(pctx, &params) <= 0) {
		EVP_PKEY_CTX_free(pctx);
		return 0;
	}
	EVP_PKEY_CTX_free(pctx);

	// pasul 2: generam efectiv perechea de chei folosind acei parametri
	EVP_PKEY_CTX* kctx = EVP_PKEY_CTX_new(params, NULL);
	EVP_PKEY_free(params);
	if (!kctx) return 0;

	if (EVP_PKEY_keygen_init(kctx) <= 0) {
		EVP_PKEY_CTX_free(kctx);
		return 0;
	}

	EVP_PKEY* pkey = NULL;
	if (EVP_PKEY_keygen(kctx, &pkey) <= 0) {
		EVP_PKEY_CTX_free(kctx);
		return 0;
	}
	EVP_PKEY_CTX_free(kctx);

	// pasul 3: extragem octetii bruti din EVP_PKEY (opac) prin interfata EC specifica --
	// EVP nu ofera direct "da-mi cei 32/65 bytes" pentru chei EC generice.
	EC_KEY* ec_key = EVP_PKEY_get1_EC_KEY(pkey);
	if (!ec_key) {
		EVP_PKEY_free(pkey);
		return 0;
	}

	const BIGNUM* priv_bn = EC_KEY_get0_private_key(ec_key);
	const EC_POINT* pub_point = EC_KEY_get0_public_key(ec_key);
	const EC_GROUP* group = EC_KEY_get0_group(ec_key);

	if (priv_bn && pub_point && group) {
		// cheia privata: BIGNUM -> exact 32 bytes big-endian, cu padding de zerouri la
		// stanga daca e nevoie (BN_bn2bin simplu ar putea produce MAI PUTIN de 32 bytes
		// daca primul byte e 0 -- ar strica orice offset fix bazat pe PRIVATE_KEY_SIZE)
		int priv_ok = (BN_bn2binpad(priv_bn, private_key_out, PRIVATE_KEY_SIZE) == PRIVATE_KEY_SIZE);

		// cheia publica: punctul de pe curba -> forma necomprimata (0x04 + x + y) = 65 bytes
		size_t written = EC_POINT_point2oct(group, pub_point, POINT_CONVERSION_UNCOMPRESSED,
			public_key_out, PUBLIC_KEY_SIZE, NULL);

		success = priv_ok && (written == PUBLIC_KEY_SIZE);
	}

	EC_KEY_free(ec_key);
	EVP_PKEY_free(pkey);
	return success;
}

static EC_KEY* ec_key_from_private(const unsigned char* private_key) {
	EC_KEY* ec_key = EC_KEY_new_by_curve_name(NID_secp256k1);
	if (!ec_key) return NULL;

	BIGNUM* priv_bn = BN_bin2bn(private_key, PRIVATE_KEY_SIZE, NULL);
	if (!priv_bn) { EC_KEY_free(ec_key); return NULL; }

	int ok = EC_KEY_set_private_key(ec_key, priv_bn);
	BN_free(priv_bn);

	if (!ok) { EC_KEY_free(ec_key); return NULL; }
	return ec_key;
}

static EC_KEY* ec_key_from_public(const unsigned char* public_key) {
	EC_KEY* ec_key = EC_KEY_new_by_curve_name(NID_secp256k1);
	if (!ec_key) return NULL;

	const EC_GROUP* group = EC_KEY_get0_group(ec_key);
	EC_POINT* pub_point = EC_POINT_new(group);
	if (!pub_point) { EC_KEY_free(ec_key); return NULL; }

	int ok = EC_POINT_oct2point(group, pub_point, public_key, PUBLIC_KEY_SIZE, NULL);
	if (ok) ok = EC_KEY_set_public_key(ec_key, pub_point);
	EC_POINT_free(pub_point);

	if (!ok) { EC_KEY_free(ec_key); return NULL; }
	return ec_key;
}

int sign_hash(const unsigned char* private_key, const unsigned char hash[32], unsigned char* signature_out) {
	EC_KEY* ec_key = ec_key_from_private(private_key);
	if (!ec_key) return 0;

	ECDSA_SIG* sig = ECDSA_do_sign(hash, 32, ec_key);
	EC_KEY_free(ec_key);
	if (!sig) return 0;

	const BIGNUM* r = NULL;
	const BIGNUM* s = NULL;
	ECDSA_SIG_get0(sig, &r, &s);

	int r_ok = (BN_bn2binpad(r, signature_out, 32) == 32);
	int s_ok = (BN_bn2binpad(s, signature_out + 32, 32) == 32);

	ECDSA_SIG_free(sig);
	return r_ok && s_ok;
}

int verify_hash_signature(const unsigned char* public_key, const unsigned char hash[32], const unsigned char* signature) {
	EC_KEY* ec_key = ec_key_from_public(public_key);
	if (!ec_key) return 0;

	BIGNUM* r = BN_bin2bn(signature, 32, NULL);
	BIGNUM* s = BN_bin2bn(signature + 32, 32, NULL);
	int result = 0;

	if (r && s) {
		ECDSA_SIG* sig = ECDSA_SIG_new();
		if (sig) {
			// ECDSA_SIG_set0 preia ownership-ul lui r si s -- nu le mai eliberam separat
			if (ECDSA_SIG_set0(sig, r, s)) {
				result = (ECDSA_do_verify(hash, 32, sig, ec_key) == 1);
			}
			else {
				BN_free(r); BN_free(s);
			}
			ECDSA_SIG_free(sig);
		}
		else {
			BN_free(r); BN_free(s);
		}
	}
	else {
		if (r) BN_free(r);
		if (s) BN_free(s);
	}

	EC_KEY_free(ec_key);
	return result;
}
