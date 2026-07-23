"""
Ruleaza toate testele Python din network/tests/, impotriva unui nod deja
pornit, si raporteaza un rezumat.

Ruleaza:
    python network/tests/run_all.py <p2p_port> <api_port> <rol: MINER|RELAY>

Exemplu, cu nodul pornit ca "python node.py 9001":
    python network/tests/run_all.py 9001 10001 MINER
"""
import sys

import test_get_info
import test_signature_rejection_http
import test_sign_and_send_http


def main():
    if len(sys.argv) < 4:
        print("Utilizare: python run_all.py <p2p_port> <api_port> <rol: MINER|RELAY>")
        sys.exit(1)

    p2p_port = int(sys.argv[1])
    api_port = int(sys.argv[2])
    role = sys.argv[3].upper()

    print("=== Teste Python (integrare, impotriva nodului real) ===\n")

    results = {
        "test_get_info": test_get_info.run(p2p_port, api_port, role),
        "test_signature_rejection_http": test_signature_rejection_http.run(api_port),
        "test_sign_and_send_http": test_sign_and_send_http.run(api_port),
    }

    passed = sum(1 for ok in results.values() if ok)
    total = len(results)
    print(f"\n--- Rezultat: {passed}/{total} teste trecute ---")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()