"""
Test: o semnatura alterata (un singur byte schimbat) trebuie respinsa
de POST /transactions, cu status 400.

Precondiie: nodul e deja pornit, si exista portofelele "alice"/"bob"
in wallets/ (ruleaza wallet.py genereaza alice / genereaza bob daca nu
exista inca).

Ruleaza:
    python network/tests/test_signature_rejection_http.py <api_port>
"""
import sys
import os
import ctypes
import base64

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # network/
sys.path.insert(0, os.path.dirname(__file__))  # tests/ -- pt http_client

from wallet_keys import load_private_key, load_public_key
from http_client import http_post

SIGNATURE_SIZE = 64  # r(32) + s(32), vezi core/include/wallet.h

DLL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "core", "build", "blockchain_core.dll")
DLL_PATH = os.path.abspath(DLL_PATH)
lib = ctypes.CDLL(DLL_PATH)
lib.sign_transaction_raw.argtypes = [
    ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint64, ctypes.c_char_p, ctypes.c_char_p
]
lib.sign_transaction_raw.restype = ctypes.c_int


def run(api_port):
    priv = load_private_key("alice")
    sender_pub = load_public_key("alice")
    receiver_pub = load_public_key("bob")
    amount = 999

    signature = ctypes.create_string_buffer(SIGNATURE_SIZE)
    if not lib.sign_transaction_raw(sender_pub, receiver_pub, amount, priv, signature):
        print("[FAIL] test_signature_rejection_http -- semnare esuata, nu putem testa respingerea")
        return False

    altered = bytearray(signature.raw)
    altered[0] ^= 0xFF  # stricam deliberat un singur byte

    payload = {
        "sender": base64.b64encode(sender_pub).decode("ascii"),
        "receiver": base64.b64encode(receiver_pub).decode("ascii"),
        "amount": amount,
        "signature": base64.b64encode(bytes(altered)).decode("ascii"),
    }

    status, data = http_post(api_port, "/transactions", payload)

    if status == 400 and "error" in data:
        print(f"[PASS] test_signature_rejection_http -- respins corect ({data['error']})")
        return True

    print(f"[FAIL] test_signature_rejection_http -- asteptam 400, am primit {status}: {data}")
    return False


if __name__ == "__main__":
    api_port = int(sys.argv[1]) if len(sys.argv) > 1 else 10001
    ok = run(api_port)
    sys.exit(0 if ok else 1)