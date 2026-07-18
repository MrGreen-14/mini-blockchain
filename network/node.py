import socket
import sys
from protocol import receive_message,send_message
from mempool import Mempool

def handle_message(msg: dict,mempool: Mempool) -> dict:
    msg_type = msg.get("type")

    if msg_type == "NEW_TRANSACTION":
        tx = msg["data"]
        mempool.add_transaction(tx["sender"],tx["receiver"],tx["amount"])
        print(f"Tranzactie adaugata: {tx}. Marime mempool: {mempool.size()}")
        return {"type": "ACK", "data": "tranzactie primita"}

    print(f"Tip de mesaj necunoscut: {msg_type}")
    return {"type": "ERROR", "data": f"tip necunoscut: {msg_type}"}

def run_node(host: str, port: int):
    mempool = Mempool()

    server_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((host, port))
    server_sock.listen()
    print(f"Nod pornit, ascult pe {host}:{port}...")

    try:
        while True:
            conn, addr = server_sock.accept()
            print(f"Conexiune noua de la {addr}")
            try:
                msg = receive_message(conn)
                response = handle_message(msg,mempool)
                send_message(conn,response)
            except ConnectionError as e:
                print(f"Conexiune inchisa neasteptat: {e}")
            finally:
                conn.close()
    except KeyboardInterrupt:
        print("\nOprire nod (Ctrl+C primit)...")
    finally:
        server_sock.close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9001
    run_node("127.0.0.1", port)



