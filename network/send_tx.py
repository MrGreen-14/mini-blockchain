#   python wallet.py genereaza alice
#   python wallet.py genereaza bob
#   python network/test_http_transaction.py alice bob 100 10001

import ctypes
import os
import sys
import base64
import json

from wallet_keys import PRIVATE_KEY_SIZE, PUBLIC_KEY_SIZE, load_private_key, load_public_key

SIGNATURE_SIZE = 64

dll_path = os.path.join(os.path.dirname(__file__), "..", "core", "build", "blockchain_core.dll")
dll_path = os.path.abspath(dll_path)
lib = ctypes.CDLL(dll_path)

lib.sign_transaction_raw.argtypes = [
    ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint64, ctypes.c_char_p, ctypes.c_char_p
]
lib.sign_transaction_raw.restype = ctypes.c_int

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