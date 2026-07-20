import struct, sys
sys.path.insert(0, ".")
from chain_format import parse_chain, BLOCKCHAIN_MAGIC, BLOCKCHAIN_VERSION, HASH_SIZE, ADDRESS_SIZE
from chain_format import find_orphaned_transactions
from consensus import resolve_fork,ForkResolution

def fixed(s, size):     
    b = s.encode("ascii")
    return b + b"\x00" * (size - len(b))

def build_block(index, prev_hash, merkle_root, nonce, block_hash, transactions=()):
    buf = struct.pack("<I", index) + struct.pack("<Q", 0)
    buf += fixed(prev_hash, HASH_SIZE) + fixed(merkle_root, HASH_SIZE)
    buf += struct.pack("<I", nonce) + fixed(block_hash, HASH_SIZE)
    buf += struct.pack("<Q", len(transactions))
    for sender, receiver, amount in transactions:
        buf += fixed(sender, ADDRESS_SIZE) + fixed(receiver, ADDRESS_SIZE) + struct.pack("<Q", amount)
    return buf

def build_chain(block_buffers):
    buf = struct.pack("<II", BLOCKCHAIN_MAGIC, BLOCKCHAIN_VERSION)
    buf += struct.pack("<Q", len(block_buffers))
    for b in block_buffers:
        buf += b
    return buf

GENESIS_PREV = "0" * 64

# b0 = build_block(0, GENESIS_PREV, "merkle0", 111, "hash0",
#                   transactions=[("COINBASE", "Miner-A", 50)])
# chain_bytes = build_chain([b0])

# b0 = build_block(0, GENESIS_PREV, "merkle0", 1, "hash0", transactions=[])
# b1_old = build_block(1, "hash0", "m1", 10, "hashA", transactions=[("X", "Y", 100)])
# b2_old = build_block(2,"hashA","m1a",15,"hashB2",transactions=[("Done","Noemi",20)])
# b1_new = build_block(1, "hash0", "m1b", 20, "hashB", transactions=[("MrGreen","Laza",69)])

# old_blocks = parse_chain(build_chain([b0, b1_old,b2_old]))
# new_blocks = parse_chain(build_chain([b0, b1_new]))

# orphaned = find_orphaned_transactions(old_blocks,new_blocks)
# print("orfane:", orphaned)

# print("Nivel 3 OK")


class LenLib:
    def is_chain_valid(self, buf):
        return 1
    def get_chain_length(self, buf):
        return len(parse_chain(buf))

# lantul local (vechi)
b0 = build_block(0, GENESIS_PREV, "m0", 1, "hash0",
                  transactions=[("COINBASE", "Miner-local", 50)])
b1_old = build_block(1, "hash0", "m1_old", 10, "hash1_OLD",
                      transactions=[("Alice", "Bob", 10), ("Carol", "Dave", 5)])
local_bytes = build_chain([b0, b1_old])

# lantul primit (nou, mai lung)
b1_new = build_block(1, "hash0", "m1_new", 20, "hash1_NEW",
                      transactions=[("Alice", "Bob", 10)])
b2_new = build_block(2, "hash1_NEW", "m2", 30, "hash2",
                      transactions=[("COINBASE", "Miner-castigator", 50)])
received_bytes = build_chain([b0, b1_new, b2_new])

lib = LenLib()
decision, local_len, received_len = resolve_fork(lib, local_bytes, received_bytes)
print("decizie:", decision, "local:", local_len, "primit:", received_len)

if decision == ForkResolution.ADOPTED:
    old_blocks = parse_chain(local_bytes)
    new_blocks = parse_chain(received_bytes)
    orphaned = find_orphaned_transactions(old_blocks, new_blocks)
    print("tranzactii orfane de recuperat:", orphaned)
    assert orphaned == [("Carol", "Dave", 5)]

print("Nivel 4 OK")