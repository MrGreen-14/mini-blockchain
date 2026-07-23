import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import socket
import time
import ctypes
import threading
import base64
from enum import Enum

from api.app import create_app
from protocol import receive_message,send_message
from mempool import Mempool
from consensus import ForkResolution, resolve_fork
from chain_format import parse_chain,find_orphaned_transactions
from chain_format import ADDRESS_SIZE, SIGNATURE_SIZE

DIFFICULTY = 5
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
    ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint64, ctypes.c_char_p
]
lib.add_transaction_to_block.restype = None

lib.verify_transaction_signature_raw.argtypes = [
    ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint64, ctypes.c_char_p
]
lib.verify_transaction_signature_raw.restype = ctypes.c_int

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


class NodeState(Enum):
    SYNCING = "SYNCING"
    SYNCED = "SYNCED"

class Node:
    def __init__(self,host,port,peers,is_miner=True):
        self.host = host
        self.port = port
        self.peers = peers
        self.is_miner = is_miner
        self.miner_address = f"Miner-{port}".encode("utf-8")

        self.mempool = Mempool()
        self.chain = lib.create_blockchain_heap()
        self.chain_lock = threading.Lock()
        self.stop_flag = ctypes.c_int(0)
        self.state = NodeState.SYNCING

    #---Mining---

    def mining_loop(self):
        while True:
            pending = self.mempool.get_pending(max_count=MAX_TX_PER_BLOCK)
            if not pending:
                time.sleep(1)
                continue
            with self.chain_lock:
                pending = self.mempool.get_pending(max_count=MAX_TX_PER_BLOCK)
                if not pending:
                    continue
                block = lib.begin_block(self.chain)
                lib.add_coinbase_transaction(block,self.miner_address,BLOCK_REWARD)
                for sender,receiver,amount, signature in pending:
                   lib.add_transaction_to_block(block, sender, receiver, amount, signature)

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
        def _send():
            for peer_host, peer_port in self.peers:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(3)
                    sock.connect((peer_host, peer_port))
                    send_message(sock, {"type": "NEW_BLOCK", "data": encoded})
                    receive_message(sock)
                    sock.close()
                except OSError as e:
                    print(f"Nu am putut trimite catre peer {peer_host}:{peer_port}: {e}")
        threading.Thread(target=_send, daemon=True).start()

    def broadcast_new_transaction(self, sender, receiver, amount, signature):
        payload = {
            "type": "NEW_TRANSACTION",
            "data": {
                "sender": base64.b64encode(sender).decode("ascii"),
                "receiver": base64.b64encode(receiver).decode("ascii"),
                "amount": amount,
                "signature": base64.b64encode(signature).decode("ascii"),
            }
        }
        def _send():
            for peer_host, peer_port in self.peers:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(3)
                    sock.connect((peer_host, peer_port))
                    send_message(sock, payload)
                    receive_message(sock)
                    sock.close()
                except OSError as e:
                    print(f"Nu am putut trimite tranzactia catre peer {peer_host}:{peer_port}: {e}")
        threading.Thread(target=_send, daemon=True).start()

    def sync_with_peers(self):
        print(f"[{self.port}] SYNCING: interoghez {len(self.peers)} peer(i)...")
        for peer_host, peer_port in self.peers:
            try:
                sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((peer_host,peer_port))
                send_message(sock,{"type":"GET_CHAIN"})
                response = receive_message(sock)
                sock.close()
            except OSError as e:
                print(f"[{self.port}] Peer {peer_host}:{peer_port} indisponibil la sincronizare: {e}")
                continue

            if response.get("type") != "CHAIN_RESPONSE":
                continue

            chain_bytes = base64.b64decode(response["data"])

            with self.chain_lock:
                new_chain = lib.deserialize_chain(chain_bytes, len(chain_bytes))
                decision, local_len, received_len = resolve_fork(lib, self.chain, new_chain)

                if decision == ForkResolution.ADOPTED:
                    old_chain = self.chain
                    self.chain = new_chain
                    lib.destroy_blockchain(old_chain)
                    print(f"[{self.port}] SYNCING: adoptat lant de {received_len} blocuri "
                          f"de la {peer_host}:{peer_port} (aveam {local_len}).")
                else:
                    lib.destroy_blockchain(new_chain)

        self.state = NodeState.SYNCED
        print(f"[{self.port}] SYNCED -- incep minarea.")

# ---------------- Handling mesaje primite ----------------
    def receive_transaction(self, sender, receiver, amount, signature):
        if len(sender) != ADDRESS_SIZE or len(receiver) != ADDRESS_SIZE:
            return False, "adresa cu lungime invalida"
        if len(signature) != SIGNATURE_SIZE:
            return False, "semnatura cu lungime invalida"
        if not lib.verify_transaction_signature_raw(sender, receiver, amount, signature):
            return False, "semnatura invalida"

        tx = (sender, receiver, amount, signature)
        if tx in self.mempool.get_pending():
            return True, None

        self.mempool.add_transaction(sender, receiver, amount, signature)
        print(f"Tranzactie adaugata (semnatura valida). Marime mempool: {self.mempool.size()}")
        self.broadcast_new_transaction(sender, receiver, amount, signature)
        return True, None

    def handle_message(self,msg):
        msg_type = msg.get("type")

        if msg_type == "NEW_TRANSACTION":
            tx = msg["data"]
            try:
                sender = base64.b64decode(tx["sender"])
                receiver = base64.b64decode(tx["receiver"])
                amount = tx["amount"]
                signature = base64.b64decode(tx["signature"])
            except (KeyError, ValueError, TypeError) as e:
                return {"type": "ERROR", "data": f"tranzactie malformata: {e}"}

            ok, error = self.receive_transaction(sender, receiver, amount, signature)
            if not ok:
                print(f"Tranzactie respinsa: {error}")
                return {"type": "ERROR", "data": error}
            return {"type": "ACK", "data": "tranzactie primita"}

        if msg_type == "NEW_BLOCK" :
            chain_bytes = base64.b64decode(msg["data"])
            # oprim minarea curenta imediat -- indiferent daca vom accepta
            # sau nu lantul primit, altfel riscam use-after-free pe lantul vechi
            self.stop_flag.value = 1

            with self.chain_lock:
                new_chain = lib.deserialize_chain(chain_bytes,len(chain_bytes))
                decision, local_len, received_len = resolve_fork(lib,self.chain,new_chain)

                if decision == ForkResolution.REJECTED_INVALID:
                    if new_chain:
                        lib.destroy_blockchain(new_chain)
                    print("Lant primit invalid, ignorat.")
                    return {"type": "ERROR", "data": "chain invalid"}

                if decision == ForkResolution.REJECTED_SHORTER:
                    lib.destroy_blockchain(new_chain)
                    print(f"Lant primit ({received_len}) nu e mai lung ({local_len}), ignorat.")
                    return {"type": "ACK", "data": "block procesat"}

                old_ptr = ctypes.c_void_p()
                old_len = lib.serialize_chain(self.chain,ctypes.byref(old_ptr))
                old_chain_bytes = ctypes.string_at(old_ptr,old_len)
                lib.free_serialized_buffer(old_ptr)

                # Serializeaza noul lant INAINTE de a parsa blocurile
                # (avem deja chain_bytes din mesajul primit)
                old_chain_handle = self.chain
                self.chain = new_chain
                lib.destroy_blockchain(old_chain_handle)
                print(f"Lant adoptat: {received_len} blocuri (anterior {local_len}).")

                # NOU: curata din mempool tranzactiile care sunt deja in lantul adoptat
                # (altfel raman in mempool si se mineaza din nou la infinit)
                adopted_blocks = parse_chain(chain_bytes)
                mined_txs = set()
                for block in adopted_blocks:
                    for tx_tuple in block["transactions"]:
                        mined_txs.add(tx_tuple)
                pending = self.mempool.get_pending()
                for tx in pending:
                    if tx in mined_txs:
                        self.mempool.remove_transactions([tx])

            old_blocks = parse_chain(old_chain_bytes)
            new_blocks = parse_chain(chain_bytes)
            orphaned_txs = find_orphaned_transactions(old_blocks, new_blocks)

            if orphaned_txs:
                for sender, receiver, amount, signature in orphaned_txs:
                    self.mempool.add_transaction(sender, receiver, amount, signature)
                print(f"{len(orphaned_txs)} tranzactii orfane repuse in mempool.")

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

    def run_api(self,api_port):
        app = create_app(self,lib)
        app.run(host="0.0.0.0",port=api_port,use_reloader=False)

    def run(self,api_port=None):
        listener_thread = threading.Thread(target=self.listen_loop, daemon=True)
        listener_thread.start()

        
        if api_port:
            api_thread=threading.Thread(
                target=self.run_api,args=(api_port,),daemon=True
            )
            api_thread.start()
        
        self.sync_with_peers()

        if self.is_miner:
            miner_thread = threading.Thread(target=self.mining_loop, daemon=True)
            miner_thread.start()
            print(f"[{self.port}] Rol: MINER")
        else:
            print(f"[{self.port}] Rol: RELAY (nu mineaza, doar propaga)")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nOprire nod (Ctrl+C primit)...")
    

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

    # al treilea argument optional: "relay" = nu mineaza
    is_miner = True
    if len(sys.argv) > 3 and sys.argv[3] == "relay":
        is_miner = False

    #portul API = portul P2P + 1000 / (9001 -> API pe 10001)
    api_port = port + 1000
    node = Node("127.0.0.1", port, peers, is_miner=is_miner)
    node.run(api_port=api_port)
