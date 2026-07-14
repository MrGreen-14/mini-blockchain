#include "merkle.h"
#include "sha256.h"
#include <cstring>
#include <cstdlib>
#include <cstdio>

static void hash_transaction(const Transaction* tx, char output_hex[65]) {
	char buffer[256];
	serialize_transaction(tx, buffer, sizeof(buffer));
	compute_sha256_hex((const unsigned char*)buffer, strlen(buffer), output_hex);
}

void compute_merkle_root(const Transaction* transactions, size_t count, char output_hex[65]) {
	if (count == 0) {
		compute_sha256_hex((const unsigned char*)"", 0, output_hex);
		return;
	}

	char** current_level = (char**)malloc(count * sizeof(char*));
	for (size_t i = 0; i < count; i++){
		current_level[i] = (char*)malloc(65);
		hash_transaction(&transactions[i], current_level[i]);
	}

	size_t level_count = count;

	while (level_count > 1) {
		size_t next_count = (level_count + 1) / 2;
		char** next_level = (char**)malloc(next_count * sizeof(char*));

		for (size_t i = 0; i < next_count; i++){
			char combined[130];
			size_t left = 2 * i;
			size_t right = (2 * i + 1 < level_count) ? (2 * i + 1) : (2 * i);

			snprintf(combined, sizeof(combined), "%s%s", current_level[left], current_level[right]);

			next_level[i] = (char*)malloc(65);
			compute_sha256_hex((const unsigned char*)combined, strlen(combined), next_level[i]);
		}

		for (size_t i = 0; i < level_count; i++) {
			free(current_level[i]);
		}
		free(current_level);

		current_level = next_level;
		level_count = next_count;
	}
	strncpy(output_hex, current_level[0], 65);
	output_hex[64] = '\0';

	free(current_level[0]);
	free(current_level);
}