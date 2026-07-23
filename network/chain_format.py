import struct

HASH_SIZE = 65
ADDRESS_SIZE = 65
SIGNATURE_SIZE = 64  # r(32) + s(32)

BLOCKCHAIN_MAGIC = 0x424C4B43
BLOCKCHAIN_VERSION = 1


def _read_fixed_str(buffer, offset, size):
    raw = buffer[offset: offset + size] # Sintaxa slicing: [start:stop]
    end = raw.find(b"\x00")
    if end == -1:
        end = size
    return raw[:end].decode("ascii"), offset + size

def _read_fixed_bytes(buffer,offset,size):
    raw = buffer[offset: offset + size]
    return raw, offset + size

def parse_chain(buffer: bytes):
    offset = 0
    magic, version = struct.unpack_from("<II", buffer, offset) # < - litle-endian;I - unsigned int;I - citeste 8 bytes si imparte in 4 si 4 bytes
    offset += 8

    if magic != BLOCKCHAIN_MAGIC:
        raise ValueError(f"Magic invalid: {magic:#x}")
    if version != BLOCKCHAIN_VERSION:
        raise ValueError(f"Versiune de format necunoscuta: {version}")

    (block_count,) = struct.unpack_from("<Q", buffer, offset)
    offset += 8

    blocks = []
    for _ in range(block_count):
        index, = struct.unpack_from("<I", buffer, offset)
        offset += 4

        # timestamp-ul e citit doar ca sa avansam offset-ul corect --
        # nu ne intereseaza valoarea pentru gasirea tranzactiilor orfane
        _timestamp, = struct.unpack_from("<Q", buffer, offset)
        offset += 8

        prev_hash, offset = _read_fixed_str(buffer, offset, HASH_SIZE)
        merkle_root, offset = _read_fixed_str(buffer, offset, HASH_SIZE)

        nonce, = struct.unpack_from("<I", buffer, offset)
        offset += 4

        block_hash, offset = _read_fixed_str(buffer, offset, HASH_SIZE)

        tx_count, = struct.unpack_from("<Q", buffer, offset)
        offset += 8

        transactions = []
        for _ in range(tx_count):
            sender, offset = _read_fixed_bytes(buffer, offset, ADDRESS_SIZE)
            receiver, offset = _read_fixed_bytes(buffer, offset, ADDRESS_SIZE)
            amount, = struct.unpack_from("<Q", buffer, offset)
            offset += 8
            signature, offset = _read_fixed_bytes(buffer, offset, SIGNATURE_SIZE)
            transactions.append((sender, receiver, amount, signature))

        blocks.append({
            "index": index,
            "prev_hash": prev_hash,
            "merkle_root": merkle_root,
            "nonce": nonce,
            "hash": block_hash,
            "transactions": transactions,
        })

    return blocks

def find_orphaned_transactions(old_blocks, new_blocks):
    new_hash_by_index = {b["index"]: b["hash"] for b in new_blocks}

    new_tx_set = {
        tx
        for block in new_blocks
        for tx in block["transactions"]
    }

    orphaned = []
    for block in old_blocks:
        still_shared = (
            block["index"] in new_hash_by_index
            and new_hash_by_index[block["index"]] == block["hash"]
        )
        if still_shared:
            continue

        for tx in block["transactions"]:
            sender = tx[0]
            if sender.startswith(b"COINBASE"):
                continue
            if tx in new_tx_set:
                continue
            orphaned.append(tx)

    return orphaned