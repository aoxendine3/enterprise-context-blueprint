import socket
import binascii
from cryptography.hazmat.primitives.asymmetric import ed25519

# The derived key from earlier
priv_hex = "33a12853e8d537091fef1b9bc4a4a61682689b5eda753e42996a15d8fb6bc2bc"
priv_bytes = binascii.unhexlify(priv_hex)
# ed25519 in cryptography library requires the exact 32 bytes seed for Ed25519PrivateKey.from_private_bytes
try:
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)
except Exception as e:
    print(f"Error loading key: {e}")
    import sys; sys.exit(1)

payload = b'{"agent":"MAXX","action":"HANDSHAKE_INIT","target":"WINDOWS_VISUAL_CORTEX"}'
signature = private_key.sign(payload)
sig_hex = binascii.hexlify(signature).decode()

packet = f"{sig_hex}|".encode() + payload

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", 8787))
    s.sendall(packet)
    response = s.recv(1024)
    print("M4 -> Visual Cortex Handshake Result:", response.decode().strip())
    s.close()
except Exception as e:
    print(f"Socket error: {e}")
