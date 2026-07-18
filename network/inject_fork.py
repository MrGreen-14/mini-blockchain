import socket
import sys
import base64
from protocol import send_message, receive_message

HOST = "127.0.0.1"
SOURCE_PORT = int(sys.argv[1])
TARGET_PORT = int(sys.argv[2])

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, SOURCE_PORT))
send_message(sock, {"type": "GET_CHAIN"})
response = receive_message(sock)
sock.close()

chain_data = response["data"]

sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock2.connect((HOST, TARGET_PORT))
send_message(sock2, {"type": "NEW_BLOCK", "data": chain_data})
result = receive_message(sock2)
sock2.close()

print(f"Lantul de la nodul {SOURCE_PORT} trimis catre nodul {TARGET_PORT}: {result}")