import ctypes
import os
import sys
import socket
import base64
import binascii

from protocol import send_message, receive_message

from wallet_keys import PRIVATE_KEY_SIZE, PUBLIC_KEY_SIZE, load_private_key, load_public_key, save_keypair

SIGNATURE_SIZE = 64

dll_path = os.path.join(os.path.dirname(__file__), "..", "core", "build", "blockchain_core.dll")
dll_path = os.path.abspath(dll_path)
lib = ctypes.CDLL(dll_path)

lib.generate_keypair.argtypes = [ctypes.c_char_p, ctypes.c_char_p]

lib.sign_transaction_raw.argtypes = [
    ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint64, ctypes.c_char_p, ctypes.c_char_p
]
lib.sign_transaction_raw.restype = ctypes.c_int

def generate_and_save_keypair(name):
    priv = ctypes.create_string_buffer(PRIVATE_KEY_SIZE)
    pub = ctypes.create_string_buffer(PUBLIC_KEY_SIZE)

    if not lib.generate_keypair(priv, pub):
        raise RuntimeError("Generare chei esuata")

    priv_path, pub_path = save_keypair(name, priv.raw, pub.raw)

    print(f"Chei generate: {priv_path} (SECRETA -- nu o trimite niciodata), {pub_path} (adresa publica)")
    print(f"Adresa (hex): {priv.raw and pub.raw.hex()}")

def send_signed_transaction(host, port, sender_priv, sender_pub, receiver_pub, amount):
    signature = ctypes.create_string_buffer(SIGNATURE_SIZE)

    if not lib.sign_transaction_raw(sender_pub, receiver_pub, amount, sender_priv, signature):
        raise RuntimeError("Semnare tranzactie esuata")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    send_message(sock,{
        "type": "NEW_TRANSACTION",
        "data":{
            "sender": base64.b64encode(sender_pub).decode("ascii"),
            "receiver": base64.b64encode(receiver_pub).decode("ascii"),
            "amount": amount,
            "signature": base64.b64encode(signature.raw).decode("ascii"),
        }
    })
    response = receive_message(sock)
    sock.close()
    return response

if __name__ == "__main__":
    comanda = sys.argv[1]

    if comanda == "genereaza":
        generate_and_save_keypair(sys.argv[2])

    elif comanda == "trimite":
        port = int(sys.argv[2])
        nume_expeditor = sys.argv[3]
        destinatar = sys.argv[4]
        suma = int(sys.argv[5])

        priv = load_private_key(nume_expeditor)
        pub = load_public_key(nume_expeditor)
        receiver_pub = load_public_key(destinatar)

        print("Raspuns:", send_signed_transaction("127.0.0.1", port, priv, pub, receiver_pub, suma))

    else:
        print("Comanda necunoscuta: 'genereaza' sau 'trimite'.")