import ctypes
import os

dll_path = os.path.join(os.path.dirname(__file__), "..", "core", "build", "blockchain_core.dll")
dll_path = os.path.abspath(dll_path)
lib = ctypes.CDLL(dll_path)

# Semnatura functiei -- declarata manual, ca de fiecare data cu ctypes
lib.compute_sha256_hex.argtypes = [
    ctypes.c_char_p,      # const unsigned char* data
    ctypes.c_size_t,      # size_t length
    ctypes.c_char_p       # char output_hex[65]  <- buffer de OUTPUT
]
lib.compute_sha256_hex.restype = None  # void -- functia nu returneaza nimic prin return

# Datele de intrare -- un string Python trebuie codificat in bytes explicit
input_data = "mrgreen".encode("utf-8")   # b"test"

# Buffer de OUTPUT -- alocat mutabil, 65 octeti, la fel ca in C
output_buffer = ctypes.create_string_buffer(65)

# Apelul -- observa ca output_buffer e trecut ca argument, nu primit ca return
lib.compute_sha256_hex(input_data, len(input_data), output_buffer)

# output_buffer.value extrage continutul ca bytes Python, pana la primul \0
result_hash = output_buffer.value.decode("utf-8")
print(f"SHA-256({input_data}) = {result_hash}")