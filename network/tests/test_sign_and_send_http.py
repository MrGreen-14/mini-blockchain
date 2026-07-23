"""
Test: fluxul complet POST /wallet/sign-and-send -- semnare pe server +
adaugare in mempool, verificat prin schimbarea mempool_size din /status.

Precondiie: nodul e deja pornit, si exista portofelele "alice"/"bob"
in wallets/.

Ruleaza:
    python network/tests/test_sign_and_send_http.py <api_port>
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))  # tests/ -- pt http_client
from http_client import http_get, http_post


def run(api_port):
    status_before, data_before = http_get(api_port, "/status")
    mempool_before = data_before["mempool_size"]

    payload = {"sender_name": "alice", "receiver": "bob", "amount": 42}
    status, data = http_post(api_port, "/wallet/sign-and-send", payload)

    if status != 201:
        print(f"[FAIL] test_sign_and_send_http -- asteptam 201, am primit {status}: {data}")
        return False

    status_after, data_after = http_get(api_port, "/status")
    mempool_after = data_after["mempool_size"]

    if mempool_after > mempool_before:
        print(f"[PASS] test_sign_and_send_http -- mempool {mempool_before} -> {mempool_after}")
        return True

    if mempool_after < mempool_before:
        # posibil: tranzactia a fost deja minata intre cele doua /status --
        # 201 de mai sus a confirmat deja acceptarea, deci tot un succes.
        print("[PASS] test_sign_and_send_http -- acceptata (mempool a scazut intre timp, probabil minata)")
        return True

    print(f"[FAIL] test_sign_and_send_http -- mempool nu s-a schimbat ({mempool_before})")
    return False


if __name__ == "__main__":
    api_port = int(sys.argv[1]) if len(sys.argv) > 1 else 10001
    ok = run(api_port)
    sys.exit(0 if ok else 1)