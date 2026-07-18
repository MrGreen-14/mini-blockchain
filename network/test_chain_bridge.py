import ctypes
import os

dll_path = os.path.join(os.path.dirname(__file__), "..", "core", "build", "blockchain_core.dll")
dll_path = os.path.abspath(dll_path)
lib = ctypes.CDLL(dll_path)

lib.create_blockchain_heap.argtypes = []
lib.create_blockchain_heap.restype = ctypes.c_void_p

lib.destroy_blockchain.argtypes = [ctypes.c_void_p]
lib.destroy_blockchain.restype = None

lib.begin_block.argtypes = [ctypes.c_void_p]
lib.begin_block.restype = ctypes.c_void_p

lib.add_transaction_to_block.argtypes = [
    ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint64
]
lib.add_transaction_to_block.restype = None

lib.commit_block.argtypes = [ctypes.c_void_p, ctypes.c_int]
lib.commit_block.restype = None

lib.is_chain_valid.argtypes = [ctypes.c_void_p]
lib.is_chain_valid.restype = ctypes.c_int

lib.serialize_chain.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
lib.serialize_chain.restype = ctypes.c_size_t

lib.deserialize_chain.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
lib.deserialize_chain.restype = ctypes.c_void_p

lib.free_serialized_buffer.argtypes = [ctypes.c_void_p]
lib.free_serialized_buffer.restype = None

chain = lib.create_blockchain_heap()
block = lib.begin_block(chain)
lib.add_transaction_to_block(block, b"Alice", b"Bob", 100)
lib.add_transaction_to_block(block, b"Bob", b"Charlie", 40)
lib.commit_block(chain,2)

print("Lant valid dupa minare:", bool(lib.is_chain_valid(chain)))

out_ptr = ctypes.c_void_p()
length = lib.serialize_chain(chain, ctypes.byref(out_ptr))
print(f"Lant serializat: {length} octeti")

raw_bytes = ctypes.string_at(out_ptr, length)

new_chain = lib.deserialize_chain(raw_bytes, length)

if not new_chain:
    print("Deserializare esuata!")
else:
    print("Lant valid dupa round-trip prin bytes:", bool(lib.is_chain_valid(new_chain)))

# --- 4. Curatenie -- fiecare alocare e eliberata de codul care stie cum a fost facuta ---
lib.free_serialized_buffer(out_ptr)   # bufferul din serialize_chain (malloc in DLL)
lib.destroy_blockchain(chain)         # lantul original (malloc in DLL)
lib.destroy_blockchain(new_chain)     # lantul reconstruit din bytes (malloc in DLL)