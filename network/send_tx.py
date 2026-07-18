import socket
import sys
from protocol import send_message, receive_message

HOST = "127.0.0.1"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9001
sender = sys.argv[2] if len(sys.argv) > 2 else "Alice"
receiver = sys.argv[3] if len(sys.argv) > 3 else "Bob"
amount = int(sys.argv[4]) if len(sys.argv) > 4 else 100

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

send_message(sock, {
    "type": "NEW_TRANSACTION",
    "data": {"sender": sender, "receiver": receiver, "amount": amount}
})

print("Raspuns:", receive_message(sock))
sock.close()