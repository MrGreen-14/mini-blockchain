import socket
from protocol import receive_message,send_message

HOST = "127.0.0.1"
PORT = 9001

server_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server_sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
server_sock.bind((HOST,PORT))
server_sock.listen()

print(f"Server ascult pe {HOST}:{PORT}...")

conn,addr = server_sock.accept()
print(f"Conexiune acceptata de la {addr}")

msg = receive_message(conn)
print("Mesaj primit:", msg)

send_message(conn, {"type": "ACK", "data": "am primit mesajul"})

conn.close()
server_sock.close()