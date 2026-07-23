# network/test_http_transaction.py
#
# Script de test pentru Modulul 10: semneaza o tranzactie folosind
# aceleasi functii ctypes ca wallet.py, apoi tipareste o comanda curl
# gata de rulat, ca sa testezi POST /transactions fara sa scrii JSON-ul
# de mana (sender/receiver/signature sunt bytes binari, nu se pot
# tasta direct intr-un curl).
#
# Foloseste chei deja generate cu:
#   python wallet.py genereaza alice
#   python wallet.py genereaza bob
#
# Ruleaza din radacina proiectului:
#   python network/test_http_transaction.py alice bob 100 10001

import ctypes
import os
import sys
import base64
import json

PRIVATE_KEY_SIZE = 32
PUBLIC_KEY_SIZE = 65
SIGNATURE_SIZE = 64

dll_path = os.path.join(os.path.dirname(__file__), "..", "core", "build", "blockchain_core.dll")
dll_path = os.path.abspath(dll_path)
lib = ctypes.CDLL(dll_path)

lib.sign_transaction_raw.argtypes = [
    ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint64, ctypes.c_char_p, ctypes.c_char_p
]
lib.sign_transaction_raw.restype = ctypes.c_int


def load_private_key(name):
    with open(f"{name}.priv", "rb") as f:
        return f.read()


def load_public_key(name):
    with open(f"{name}.pub", "rb") as f:
        return f.read()


if __name__ == "__main__":
    sender_name = sys.argv[1]
    receiver_name = sys.argv[2]
    amount = int(sys.argv[3])
    api_port = sys.argv[4] if len(sys.argv) > 4 else "10001"

    sender_priv = load_private_key(sender_name)
    sender_pub = load_public_key(sender_name)
    receiver_pub = load_public_key(receiver_name)

    signature = ctypes.create_string_buffer(SIGNATURE_SIZE)
    ok = lib.sign_transaction_raw(sender_pub, receiver_pub, amount, sender_priv, signature)
    if not ok:
        raise RuntimeError("Semnare esuata")

    body = {
        "sender": base64.b64encode(sender_pub).decode("ascii"),
        "receiver": base64.b64encode(receiver_pub).decode("ascii"),
        "amount": amount,
        "signature": base64.b64encode(signature.raw).decode("ascii"),
    }

    # Scriem JSON-ul intr-un fisier separat, nu direct in linia de comanda.
    # Motiv: pe Windows, curl.exe (executabil nativ) parseaza argumentele
    # dupa reguli diferite fata de bash -- ghilimelele duble din interiorul
    # JSON-ului se pot corupe cand trec prin PowerShell catre curl.exe.
    # Cu --data-binary @fisier, curl citeste bytes direct din fisier,
    # fara nicio interpretare de shell -- imun la problema asta.
    out_path = os.path.join(os.path.dirname(__file__), "tx_body.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(body, f)

    print("Body JSON (scris in tx_body.json):")
    print(json.dumps(body, indent=2))
    print()
    print("Comanda curl (Windows, robusta -- citeste din fisier):")
    print(f'curl.exe -X POST http://127.0.0.1:{api_port}/transactions '
          f'-H "Content-Type: application/json" '
          f'--data-binary "@{out_path}"')