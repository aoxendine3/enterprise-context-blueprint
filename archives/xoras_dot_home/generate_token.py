#!/usr/bin/env python3
import base64, json, time, sys, os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

# Load private key
priv_path = os.path.expanduser("~/.xoras/private_key.pem")
with open(priv_path, "rb") as f:
    private_key = serialization.load_pem_private_key(f.read(), password=None)

# Simple payload: JSON with timestamp and a nonce
payload_dict = {"iat": int(time.time()), "nonce": "bridge"}
payload_bytes = json.dumps(payload_dict, separators=(',', ':')).encode()

# Sign using RSA-PSS SHA256
signature = private_key.sign(
    payload_bytes,
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH,
    ),
    hashes.SHA256(),
)

# Base64‑url encode without padding
payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode().rstrip('=')
sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip('=')

token = f"{payload_b64}.{sig_b64}"

# Write token file
token_path = os.path.expanduser("~/.xoras/token")
with open(token_path, "w") as f:
    f.write(token)

print("Token generated and written to ~/.xoras/token")
