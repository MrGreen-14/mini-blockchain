# network/wallet_keys.py
#
# Functii comune de incarcare/salvare a cheilor de portofel, folosite
# de wallet.py (CLI), test_http_transaction.py, si (in curand) de
# api/app.py pentru semnare direct din UI. Extrase intr-un singur loc
# ca sa nu existe doua copii ale aceleiasi logici care pot ajunge sa
# difere in timp -- acelasi principiu deja aplicat in proiect la
# sha256/merkle/mining (fiecare modul, o singura responsabilitate).

import os
import binascii

PRIVATE_KEY_SIZE = 32
PUBLIC_KEY_SIZE = 65

WALLETS_DIR = os.path.join(os.path.dirname(__file__), "..", "wallets")
WALLETS_DIR = os.path.abspath(WALLETS_DIR)


def load_private_key(name):
    path = os.path.join(WALLETS_DIR, f"{name}.priv")
    with open(path, "rb") as f:
        data = f.read()
    if len(data) != PRIVATE_KEY_SIZE:
        raise ValueError(f"Fisier cheie privata corupt: {len(data)} bytes, asteptam {PRIVATE_KEY_SIZE}")
    return data


def load_public_key(name_or_hex):
    pub_path = os.path.join(WALLETS_DIR, f"{name_or_hex}.pub")
    if os.path.exists(pub_path):
        with open(pub_path, "rb") as f:
            data = f.read()
    else:
        data = binascii.unhexlify(name_or_hex)

    if len(data) != PUBLIC_KEY_SIZE:
        raise ValueError(f"Cheie publica cu lungime invalida: {len(data)} bytes, asteptam {PUBLIC_KEY_SIZE}")
    return data


def save_keypair(name, priv_bytes, pub_bytes):
    os.makedirs(WALLETS_DIR, exist_ok=True)
    priv_path = os.path.join(WALLETS_DIR, f"{name}.priv")
    pub_path = os.path.join(WALLETS_DIR, f"{name}.pub")
    with open(priv_path, "wb") as f:
        f.write(priv_bytes)
    with open(pub_path, "wb") as f:
        f.write(pub_bytes)
    return priv_path, pub_path


def list_wallet_names():
    """Numele (fara extensie) tuturor portofelelor disponibile local.
    Nu e folosit inca -- il pregatesc pentru Punctul 1, ca sa poti
    alege expeditorul dintr-un dropdown in UI, nu sa-l tastezi manual."""
    if not os.path.isdir(WALLETS_DIR):
        return []
    names = set()
    for filename in os.listdir(WALLETS_DIR):
        if filename.endswith(".priv"):
            names.add(filename[: -len(".priv")])
    return sorted(names)