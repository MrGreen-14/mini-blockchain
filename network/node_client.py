import socket
from protocol import send_message, receive_message

HOST = "127.0.0.1"
PORT = 9001

client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client_socket.connect((HOST,PORT))

send_message(client_socket,{"type":"NEW_TRANSACTION","data":
                            {"sender":"Alice", "receiver":"Bob","amount":100}
})

response = receive_message(client_socket)
print("Raspuns server:", response)
client_socket.close()