import socket
import struct
import json

def send_message(sock:socket.socket,message:dict):
    payload = json.dumps(message).encode("utf-8")
    header = struct.pack("!I",len(payload)) #! - network byte order; I - unsigned int 
    sock.sendall(header+payload)

def recv_exact(sock:socket.socket,n : int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n -len(buf))
        if not chunk:
            raise ConnectionError("Conexiune inchisa inainte de a primi toti octetii asteptati")
        buf+=chunk
    return buf

def receive_message(sock:socket.socket)-> dict:
    header = recv_exact(sock,4)
    (length,) = struct.unpack("!I",header)
    payload = recv_exact(sock,length)
    return json.loads(payload.decode("utf-8"))