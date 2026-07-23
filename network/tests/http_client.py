# network/tests/http_client.py
#
# Helper minimal pentru testele HTTP -- foloseste doar "urllib" din
# biblioteca standard. Nu adaugam "requests" ca dependenta noua --
# acelasi principiu de "zero dependente in plus" aplicat in tot
# proiectul (vezi si UI-ul, HTML/CSS/JS vanilla, fara framework).

import json
import urllib.request
import urllib.error


def http_get(api_port, path):
    url = f"http://127.0.0.1:{api_port}{path}"
    with urllib.request.urlopen(url, timeout=5) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def http_post(api_port, path, payload):
    url = f"http://127.0.0.1:{api_port}{path}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # urllib arunca exceptie pentru orice status >= 400 -- il tratam
        # ca pe un raspuns normal (nu ca pe o eroare de retea), fiindca
        # exact asta testam: ca serverul respinge corect, cu 400.
        return e.code, json.loads(e.read().decode("utf-8"))