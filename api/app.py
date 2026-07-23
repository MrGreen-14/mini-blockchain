import base64
import binascii
import ctypes
import os
import sys
from flask import Flask, request, jsonify, send_from_directory
from chain_format import parse_chain



NETWORK_DIR = os.path.join(os.path.dirname(__file__), "..", "network")
NETWORK_DIR = os.path.abspath(NETWORK_DIR)
if NETWORK_DIR not in sys.path:
    sys.path.insert(0, NETWORK_DIR)

from wallet_keys import load_private_key, load_public_key, list_wallet_names

   
ADDRESS_SIZE  = 65   # cheia publica EC (format necomprimat: 04 + 32x + 32y)
SIGNATURE_SIZE = 64  # r(32 bytes) + s(32 bytes), ECDSA/secp256k1


def create_app(node, lib):
    app = Flask(__name__)

    FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "ui")
    
    @app.route("/")
    def serve_index():
        return send_from_directory(FRONTEND_DIR, "index.html")
    
    @app.route("/<path:filename>")
    def serve_static(filename):
        return send_from_directory(FRONTEND_DIR, filename)

    lib.sign_transaction_raw.argtypes = [
        ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint64, ctypes.c_char_p, ctypes.c_char_p
        ]
    lib.sign_transaction_raw.restype = ctypes.c_int

 # ------------------------------------------------------------------ #
    #  GET /wallet/names  --  ce portofele exista local (pt dropdown UI) #
    # ------------------------------------------------------------------ #

    @app.route("/wallet/names", methods=["GET"])
    def wallet_names():
        return jsonify({"names": list_wallet_names()}), 200

 # ------------------------------------------------------------------ #
    #  GET /peers  --  interogheaza fiecare peer (rol + accesibilitate)  #
    # ------------------------------------------------------------------ #

    @app.route("/peers", methods=["GET"])
    def get_peers():
        return jsonify({"peers": node.get_peers_info()}), 200



    @app.route("/wallet/sign-and-send", methods=["POST"])
    def sign_and_send():
        data = request.get_json()
        if data is None:
            return jsonify({"error": "body-ul trebuie sa fie JSON valid"}), 400

        try:
            sender_name = data["sender_name"]
            receiver = data["receiver"]
            amount = data["amount"]
        except KeyError as e:
            return jsonify({"error": f"camp lipsa: {e}"}), 400

        try:
            sender_priv = load_private_key(sender_name)
            sender_pub = load_public_key(sender_name)
            receiver_pub = load_public_key(receiver)
        except (FileNotFoundError, ValueError, binascii.Error) as e:
            return jsonify({"error": f"portofel invalid: {e}"}), 400

        signature = ctypes.create_string_buffer(SIGNATURE_SIZE)
        if not lib.sign_transaction_raw(sender_pub, receiver_pub, amount, sender_priv, signature):
            return jsonify({"error": "semnare esuata"}), 400

        ok, error = node.receive_transaction(sender_pub, receiver_pub, amount, signature.raw)
        if not ok:
            return jsonify({"error": error}), 400

        return jsonify({
            "message": "tranzactie semnata si trimisa",
            "mempool_size": node.mempool.size()
        }), 201

    # ------------------------------------------------------------------ #
    #  POST /transactions  --  trimite o tranzactie semnata              #
    # ------------------------------------------------------------------ #
    # Echivalentul HTTP al mesajului {"type": "NEW_TRANSACTION", ...}
    # din protocol.py.  Face exact aceeasi validare ca handle_message()
    # din node.py, dar raspunde cu status code-uri HTTP in loc de
    # {"type": "ACK"} / {"type": "ERROR"}.
    #
    # Clientul trimite un JSON in body:
    # {
    #     "sender":    "<base64>",   -- cheia publica a expeditorului
    #     "receiver":  "<base64>",   -- cheia publica a destinatarului
    #     "amount":    <int>,        -- suma (in unitati intregi)
    #     "signature": "<base64>"    -- semnatura ECDSA a tranzactiei
    # }
    #
    # Raspunsuri:
    #   201 Created      -- tranzactie acceptata si adaugata in mempool
    #   400 Bad Request  -- date lipsa/invalide/semnatura esuata

    @app.route("/transactions", methods=["POST"])
    def submit_transaction():

        # --- Pasul 1: parseaza JSON-ul din body-ul HTTP ---
        # request.get_json() face ce face receive_message() + json.loads()
        # din protocol.py, dar automat -- Flask a citit deja bytes din socket,
        # a parsat headerele HTTP, si acum extrage body-ul ca dict Python.
        data = request.get_json()
        if data is None:
            return jsonify({"error": "body-ul trebuie sa fie JSON valid"}), 400

        # --- Pasul 2: extrage si decodeaza campurile ---
        # Campurile sunt base64-encoded (la fel ca in wallet.py / node.py),
        # pentru ca JSON nu poate transporta bytes bruti -- base64 transforma
        # orice secventa de bytes intr-un string ASCII sigur pentru JSON.
        try:
            sender    = base64.b64decode(data["sender"])
            receiver  = base64.b64decode(data["receiver"])
            amount    = data["amount"]
            signature = base64.b64decode(data["signature"])
        except (KeyError, ValueError, TypeError) as e:
            return jsonify({"error": f"tranzactie malformata: {e}"}), 400

        # --- Pasul 3: valideaza, adauga in mempool, si propaga catre peers ---
        # Totul (verificare lungimi, verificare semnatura, deduplicare,
        # adaugare in mempool, broadcast) e centralizat in receive_transaction(),
        # aceeasi metoda pe care o foloseste si handle_message() cand
        # tranzactia vine de la un alt nod (P2P) -- o singura sursa de adevar
        # pentru logica de business, indiferent pe unde intra tranzactia.
        ok, error = node.receive_transaction(sender, receiver, amount, signature)
        if not ok:
            return jsonify({"error": error}), 400

        return jsonify({
            "message": "tranzactie acceptata",
            "mempool_size": node.mempool.size()
        }), 201

    # ------------------------------------------------------------------ #
    #  GET /chain  --  returneaza lantul curent, ca JSON lizibil          #
    # ------------------------------------------------------------------ #
    # Lantul e stocat intern ca structura binara C (Blockchain*, in DLL).
    # Nu putem trimite bytes bruti intr-un JSON -- reutilizam parse_chain()
    # din chain_format.py (deja scrisa in Modulul 8, pentru fork resolution)
    # ca sa transformam bufferul binar intr-o lista de dict-uri Python,
    # gata de jsonify().

    @app.route("/chain", methods=["GET"])
    def get_chain():
        with node.chain_lock:
            out_ptr = ctypes.c_void_p()
            buf_len = lib.serialize_chain(node.chain, ctypes.byref(out_ptr))
            chain_bytes = ctypes.string_at(out_ptr, buf_len)
            lib.free_serialized_buffer(out_ptr)

        blocks = parse_chain(chain_bytes)

        # parse_chain() intoarce tranzactiile ca tuple de bytes bruti
        # (sender, receiver, amount) -- utile pentru comparatii interne
        # (fork resolution), dar bytes brut nu poate fi pus direct in JSON.
        # Le transformam in hex, un format text lizibil si standard pentru
        # a reprezenta bytes (fiecare byte -> 2 caractere hexa).
        for block in blocks:
            block["transactions"] = [
                {
                    "sender": sender.hex(),
                    "receiver": receiver.hex(),
                    "amount": amount,
                    "signature":signature.hex(),
                }
                for sender, receiver, amount, signature in block["transactions"]
            ]

        return jsonify({
            "length": len(blocks),
            "blocks": blocks,
        }), 200

    # ------------------------------------------------------------------ #
    #  GET /status  --  informatii rapide despre starea nodului          #
    # ------------------------------------------------------------------ #
    # Util pentru un viitor UI (Modul 11): "e nodul sincronizat? cate
    # tranzactii asteapta in mempool? cat de lung e lantul local?"
    # fara sa trebuiasca sa descarci tot lantul doar ca sa afli atat.

    @app.route("/status", methods=["GET"])
    def get_status():
        with node.chain_lock:
            length = lib.get_chain_length(node.chain)

        return jsonify({
            "state": node.state.value,
            "chain_length": length,
            "mempool_size": node.mempool.size(),
            "peers": [f"{h}:{p}" for h, p in node.peers],
        }), 200

    return app