import ctypes
import os
import socket
import time
import sys
import threading
import base64

from protocol import receive_message,send_message
from mempool import Mempool

DIFFICULTY = 4
BLOCK_REWARD = 50
MAX_TX_PER_BLOCK = 10

dll_path = os.path.join(os.path.dirname(__file__),"..","core","build","blockchain_core.dll")
dll_path = os.path.abspath(dll_path)
lib = ctypes.CDLL(dll_path)

lib.create_blockchain_heap.argtypes= []
lib.create_blockchain_heap.restype= ctypes.c_void_p

lib.destroy_blockchain.argtypes = [ctypes.c_void_p]
lib.destroy_blockchain.restype = None

lib.begin_block.argtypes=[ctypes.c_void_p]
lib.begin_block.restype = ctypes.c_void_p

lib.add_coinbase_transaction.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint64]
lib.add_coinbase_transaction.restype = None

lib.add_transaction_to_block.argtypes = [
    ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint64
]
lib.add_transaction_to_block.restype = None

lib.commit_block.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
lib.commit_block.restype = ctypes.c_int

lib.is_chain_valid.argtypes = [ctypes.c_void_p]
lib.is_chain_valid.restype = ctypes.c_int

lib.get_chain_length.argtypes = [ctypes.c_void_p]
lib.get_chain_length.restype = ctypes.c_size_t

lib.serialize_chain.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
lib.serialize_chain.restype = ctypes.c_size_t

lib.deserialize_chain.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
lib.deserialize_chain.restype = ctypes.c_void_p

lib.free_serialized_buffer.argtypes = [ctypes.c_void_p]
lib.free_serialized_buffer.restype = None

class Node:
    def __init__(self,host,port,peers):
        self.host = host
        self.port = port
        self.peers = peers
        self.miner_address = f"Miner-{port}".encode("utf-8")

        self.mempool = Mempool()
        self.chain = lib.create_blockchain_heap()
        self.chain_lock = threading.Lock()
        self.stop_flag = ctypes.c_int(0)

    #---Mining---

    def mining_loop(self):
        while True:
            pending = self.mempool.get_pending(max_count=MAX_TX_PER_BLOCK)
            if not pending:
                time.sleep(1)
                continue
            with self.chain_lock:
                block = lib.begin_block(self.chain)
                lib.add_coinbase_transaction(block,self.miner_address,BLOCK_REWARD)
                for sender,receiver,amount in pending:
                    lib.add_transaction_to_block(
                        block, sender.encode("utf-8"),receiver.encode("utf-8"),amount
                    )

                self.stop_flag.value=0
                success = lib.commit_block(self.chain, DIFFICULTY,ctypes.byref(self.stop_flag))

                if success:
                    length = lib.get_chain_length(self.chain)
                    
                    valid_before_serialize = lib.is_chain_valid(self.chain)
                    print(f"[DEBUG] Lant valid LOCAL, inainte de serializare: {bool(valid_before_serialize)}")
                    
                    out_ptr = ctypes.c_void_p()
                    buf_len = lib.serialize_chain(self.chain, ctypes.byref(out_ptr))
                    chain_bytes = ctypes.string_at(out_ptr,buf_len)
                    lib.free_serialized_buffer(out_ptr)
            if success:
                print(f"Bloc minat! Lant are acum {length} blocuri, {len(pending)} tranzactii incluse.")
                self.mempool.remove_transactions(pending)
                self.broadcast_new_block(chain_bytes)
            else:
                print("Minare intrerupta -- un alt nod a castigat cursa, reincerc pe noul lant.")

    def broadcast_new_block(self,chain_bytes):
        encoded = base64.b64encode(chain_bytes).decode("ascii")
        for peer_host,peer_port in self.peers:
            try:
                sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((peer_host,peer_port))
                send_message(sock,{"type":"NEW_BLOCK","data":encoded})
                receive_message(sock)
                sock.close()
            except OSError as e:
                print(f"Nu am putut trimite catre peer {peer_host}:{peer_port}: {e}")

# ---------------- Handling mesaje primite ----------------
    def handle_message(self,msg):
        msg_type = msg.get("type")

        if msg_type == "NEW_TRANSACTION":
            tx = msg["data"]
            self.mempool.add_transaction(tx["sender"],tx["receiver"],tx["amount"])
            print(f"Tranzactie adaugata: {tx}. Marime mempool: {self.mempool.size()}")
            return {"type": "ACK", "data": "tranzactie primita"}

        if msg_type == "NEW_BLOCK" :
            chain_bytes = base64.b64decode(msg["data"])
            # oprim minarea curenta imediat -- indiferent daca vom accepta
            # sau nu lantul primit, altfel riscam use-after-free pe lantul vechi
            self.stop_flag.value = 1

            with self.chain_lock:
                new_chain = lib.deserialize_chain(chain_bytes,len(chain_bytes))
                
                if not new_chain or not lib.is_chain_valid(new_chain):
                    if new_chain:
                        lib.destroy_blockchain(new_chain)
                    print("Lant primit invalid, ignorat.")
                    return {"type": "ERROR", "data": "chain invalid"}
                
                local_len = lib.get_chain_length(self.chain)
                received_len = lib.get_chain_length(new_chain)

                if received_len > local_len:
                    old_chain = self.chain
                    self.chain = new_chain
                    lib.destroy_blockchain(old_chain)
                    print(f"Lant adoptat: {received_len} blocuri (anterior {local_len}).")
                else:
                    lib.destroy_blockchain(new_chain)
                    print(f"Lant primit ({received_len}) nu e mai lung ({local_len}), ignorat.")
            return {"type": "ACK", "data": "block procesat"}
        
        if msg_type == "GET_CHAIN":
            with self.chain_lock:
                out_ptr = ctypes.c_void_p()
                buf_len = lib.serialize_chain(self.chain,ctypes.byref(out_ptr))
                chain_bytes = ctypes.string_at(out_ptr,buf_len)
                lib.free_serialized_buffer(out_ptr)
            encoded = base64.b64encode(chain_bytes).decode("ascii")
            return{"type":"CHAIN_RESPONSE","data": encoded}
        

        print(f"Tip de mesaj necunoscut: {msg_type}")
        return {"type": "ERROR", "data": f"tip necunoscut: {msg_type}"}
    
# ---------------- Server ----------------
    
    def listen_loop(self):
        server_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        server_sock.bind((self.host,self.port))
        server_sock.listen()
        print(f"Nod pornit, ascult pe {self.host}:{self.port}...")

        try:
            while True:
                conn,addr = server_sock.accept()
                try:
                    msg = receive_message(conn)
                    response = self.handle_message(msg)
                    send_message(conn,response)
                except ConnectionError as e:
                    print(f"Conexiune inchisa neasteptat: {e}")
                except Exception as e:
                    print(f"Eroare neasteptata la procesarea mesajului: {e}")
                finally:
                    conn.close()
        except KeyboardInterrupt:
            print("\nOprire nod (Ctrl+C primit)...")
        finally:
            server_sock.close()

    def run(self):
            miner_thread = threading.Thread(target=self.mining_loop,daemon=True)
            miner_thread.start()
            self.listen_loop()
    
def parse_peers(peers_str):
    if not peers_str:
        return []
    peers = []
    for entry in peers_str.split(","):
        host,port = entry.split(":")
        peers.append((host,int(port)))
    return peers    

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9001
    peers_arg = sys.argv[2] if len(sys.argv) > 2 else ""
    peers = parse_peers(peers_arg)

    node = Node("127.0.0.1", port, peers)
    node.run()





# def handle_message(msg: dict,mempool: Mempool) -> dict:
#     msg_type = msg.get("type")

#     if msg_type == "NEW_TRANSACTION":
#         tx = msg["data"]
#         mempool.add_transaction(tx["sender"],tx["receiver"],tx["amount"])
#         print(f"Tranzactie adaugata: {tx}. Marime mempool: {mempool.size()}")
#         return {"type": "ACK", "data": "tranzactie primita"}

#     print(f"Tip de mesaj necunoscut: {msg_type}")
#     return {"type": "ERROR", "data": f"tip necunoscut: {msg_type}"}

# def run_node(host: str, port: int):
#     mempool = Mempool()

#     server_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
#     server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     server_sock.bind((host, port))
#     server_sock.listen()
#     print(f"Nod pornit, ascult pe {host}:{port}...")

#     try:
#         while True:
#             conn, addr = server_sock.accept()
#             print(f"Conexiune noua de la {addr}")
#             try:
#                 msg = receive_message(conn)
#                 response = handle_message(msg,mempool)
#                 send_message(conn,response)
#             except ConnectionError as e:
#                 print(f"Conexiune inchisa neasteptat: {e}")
#             finally:
#                 conn.close()
#     except KeyboardInterrupt:
#         print("\nOprire nod (Ctrl+C primit)...")
#     finally:
#         server_sock.close()

# if __name__ == "__main__":
#     port = int(sys.argv[1]) if len(sys.argv) > 1 else 9001
#     run_node("127.0.0.1", port)



