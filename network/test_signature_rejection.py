import socket
import base64

from protocol import send_message, receive_message
from wallet import load_private_key, load_public_key, PRIVATE_KEY_SIZE
import ctypes
from wallet import lib, SIGNATURE_SIZE

HOST = "127.0.0.1"
PORT = 9001

priv = load_private_key("alice")
sender_pub = load_public_key("alice")
receiver_pub = load_public_key("bob")
amount = 999

signature = ctypes.create_string_buffer(SIGNATURE_SIZE)
if not lib.sign_transaction_raw(sender_pub, receiver_pub, amount, priv, signature):
    raise RuntimeError("Semnare esuata")

semnatura_alterata = bytearray(signature.raw)
semnatura_alterata[0] ^= 0xFF  # stricam un singur byte, deliberat

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
send_message(sock, {
    "type": "NEW_TRANSACTION",
    "data": {
        "sender": base64.b64encode(sender_pub).decode("ascii"),
        "receiver": base64.b64encode(receiver_pub).decode("ascii"),
        "amount": amount,
        "signature": base64.b64encode(bytes(semnatura_alterata)).decode("ascii"),
    }
})
response = receive_message(sock)
sock.close()

print("Raspuns primit:", response)
assert response["type"] == "ERROR", "EROARE: nodul a acceptat o semnatura alterata!"
print("OK -- nodul a respins corect tranzactia cu semnatura alterata.")