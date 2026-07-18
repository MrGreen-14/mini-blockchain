import ctypes
import os
import threading
import time

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

lib.mine_block.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
lib.mine_block.restype = ctypes.c_int

# --- pregatim un bloc candidat, dar NU il mai minam prin commit_block --
#     mine_block e testat izolat, direct pe block-ul deschis de begin_block
chain = lib.create_blockchain_heap()
block = lib.begin_block(chain)
lib.add_transaction_to_block(block, b"Alice", b"Bob", 100)

stop_flag = ctypes.c_int(0)

def mining_thread():
    print("Start minare (dificultate mare, ca sa dureze cateva secunde)...")
    result = lib.mine_block(block, 3, ctypes.byref(stop_flag))
    if result:
        print("A GASIT nonce inainte sa vina semnalul (mareste dificultatea si ruleaza din nou).")
    else:
        print("Minare intrerupta cu succes -- flag-ul a functionat.")

def stopper_thread():
    time.sleep(1.5)
    print("Trimit semnal de oprire...")
    stop_flag.value = 1

t1 = threading.Thread(target=mining_thread)
t2 = threading.Thread(target=stopper_thread)

t1.start()
t2.start()
t1.join()
t2.join()

lib.destroy_blockchain(chain)