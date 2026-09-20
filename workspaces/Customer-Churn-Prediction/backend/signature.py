import os
import subprocess
import base64
import tempfile

KEY_DIR = "/Users/ajoxendine68/Xoras_Enterprise_Core"
PRIVATE_KEY_PATH = os.path.join(KEY_DIR, "attestation_key.pem")
PUBLIC_KEY_PATH = os.path.join(KEY_DIR, "attestation_key.pub")

def init_keys():
    os.makedirs(KEY_DIR, exist_ok=True)
    if not os.path.exists(PRIVATE_KEY_PATH):
        # Generate private key
        subprocess.run([
            "openssl", "genpkey", "-algorithm", "RSA", 
            "-out", PRIVATE_KEY_PATH, "-pkeyopt", "rsa_keygen_bits:2048"
        ], check=True, capture_output=True)
        # Extract public key
        subprocess.run([
            "openssl", "rsa", "-pubout", 
            "-in", PRIVATE_KEY_PATH, "-out", PUBLIC_KEY_PATH
        ], check=True, capture_output=True)
        print("[SIGNATURE] New machine attestation key pair generated in Xoras_Enterprise_Core.")

def sign_payload(payload: str) -> str:
    init_keys()
    # Sign using openssl
    proc = subprocess.Popen(
        ["openssl", "dgst", "-sha256", "-sign", PRIVATE_KEY_PATH, "-binary"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = proc.communicate(input=payload.encode())
    if proc.returncode != 0:
        raise RuntimeError(f"Signing failed: {stderr.decode()}")
    return base64.b64encode(stdout).decode('utf-8')

def verify_signature(payload: str, signature_b64: str) -> bool:
    init_keys()
    try:
        sig_bytes = base64.b64decode(signature_b64)
    except Exception:
        return False

    # Verify signature using openssl. We need to pass signature as a file.
    with tempfile.NamedTemporaryFile(delete=False) as sig_file:
        sig_file.write(sig_bytes)
        sig_file_path = sig_file.name

    try:
        proc = subprocess.Popen(
            ["openssl", "dgst", "-sha256", "-verify", PUBLIC_KEY_PATH, "-signature", sig_file_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = proc.communicate(input=payload.encode())
        return proc.returncode == 0
    finally:
        if os.path.exists(sig_file_path):
            os.remove(sig_file_path)
