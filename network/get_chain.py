import socket
import sys
import base64
from protocol import send_message, receive_message

HOST = "127.0.0.1"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9001

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
send_message(sock, {"type": "GET_CHAIN"})
response = receive_message(sock)
sock.close()

if response["type"] != "CHAIN_RESPONSE":
    print("Eroare:", response)
    sys.exit(1)

chain_bytes = base64.b64decode(response["data"])
print(f"Lant primit: {len(chain_bytes)} octeti serializati.")