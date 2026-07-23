"""
Test: GET_INFO (peste conexiunea TCP P2P) raspunde cu api_port si rol
corecte -- exact mecanismul folosit de get_peers_info()/GET /peers.

Precondiie: nodul e deja pornit.

Ruleaza:
    python network/tests/test_get_info.py <p2p_port> <api_port_asteptat> <rol_asteptat>

Exemplu (nod pornit cu "python node.py 9001", deci api_port=10001, miner):
    python network/tests/test_get_info.py 9001 10001 MINER
"""
import sys
import os
import socket

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # network/
from protocol import send_message, receive_message


def run(p2p_port, expected_api_port, expected_role):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    try:
        sock.connect(("127.0.0.1", p2p_port))
        send_message(sock, {"type": "GET_INFO"})
        response = receive_message(sock)
    except OSError as e:
        print(f"[FAIL] test_get_info -- nu m-am putut conecta la portul {p2p_port}: {e}")
        return False
    finally:
        sock.close()

    if response.get("type") != "INFO_RESPONSE":
        print(f"[FAIL] test_get_info -- tip de raspuns neasteptat: {response}")
        return False

    info = response.get("data", {})
    ok = (info.get("api_port") == expected_api_port) and (info.get("role") == expected_role)

    if ok:
        print(f"[PASS] test_get_info -- api_port={info['api_port']}, role={info['role']}")
    else:
        print(
            f"[FAIL] test_get_info -- asteptam api_port={expected_api_port}/role={expected_role}, "
            f"am primit {info}"
        )
    return ok


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Utilizare: python test_get_info.py <p2p_port> <api_port_asteptat> <rol_asteptat: MINER|RELAY>")
        sys.exit(1)

    p2p_port = int(sys.argv[1])
    expected_api_port = int(sys.argv[2])
    expected_role = sys.argv[3].upper()

    ok = run(p2p_port, expected_api_port, expected_role)
    sys.exit(0 if ok else 1)