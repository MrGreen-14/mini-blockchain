import ctypes
import os
import sys
import socket
import base64
import binascii

from protocol import send_message, receive_message

PRIVATE_KEY_SIZE = 32
PUBLIC_KEY_SIZE = 65
SIGNATURE_SIZE = 64

dll_path = os.path.join(os.path.dirname(__file__), "..", "core", "build", "blockchain_core.dll")
dll_path = os.path.abspath(dll_path)
lib = ctypes.CDLL(dll_path)

lib.generate_keypair.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
lib.generate_keypair.restype = ctypes.c_int

lib.sign_transaction_raw.argtypes = [
    ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint64, ctypes.c_char_p, ctypes.c_char_p
]
lib.sign_transaction_raw.restype = ctypes.c_int

def generate_and_save_keypair(name):
    priv = ctypes.create_string_buffer(PRIVATE_KEY_SIZE)
    pub = ctypes.create_string_buffer(PUBLIC_KEY_SIZE)

    if not lib.generate_keypair(priv,pub):
        raise RuntimeError("Generare chei esuata")
    
    with open(f"{name}.priv","wb") as f:
        f.write(priv.raw)
    with open(f"{name}.pub", "wb") as f:
        f.write(pub.raw)
    
    print(f"Chei generate: {name}.priv (SECRETA -- nu o trimite niciodata), {name}.pub (adresa publica)")
    print(f"Adresa (hex): {priv.raw and pub.raw.hex()}")

def load_private_key(name):
    with open(f"{name}.priv","rb") as f:
        data = f.read()
    if len(data) != PRIVATE_KEY_SIZE:
        raise ValueError(f"Fisier cheie privata corupt: {len(data)} bytes, asteptam {PRIVATE_KEY_SIZE}")
    return data

def load_public_key(name_or_hex):
    pub_path = f"{name_or_hex}.pub"
    if os.path.exists(pub_path):
        with open(pub_path, "rb") as f:
            data = f.read()
    else:
       data = binascii.unhexlify(name_or_hex)
    
    if len(data) != PUBLIC_KEY_SIZE:
        raise ValueError(f"Cheie publica cu lungime invalida: {len(data)} bytes, asteptam {PUBLIC_KEY_SIZE}")
    return data

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