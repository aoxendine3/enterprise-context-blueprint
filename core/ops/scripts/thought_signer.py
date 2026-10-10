#!/usr/bin/env python3
"""
thought_signer.py
XORAS::OS — Cryptographic Payload Signer and Verification Gate (Ed25519)

Provides secure, off-grid key generation, deterministic payload serialization,
signing of agent thoughts/traces, and boundary signature verification.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, Tuple
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

# --- SECURE DEFAULT CONFIGURATION ---
DEFAULT_PRIVATE_KEY_PATH = "/workspace/scratch/xoras_private_key.pem"
DEFAULT_PUBLIC_KEY_PATH = "/workspace/scratch/xoras_public_key.pem"

def generate_key_pair(private_path: str, public_path: str) -> Tuple[bytes, bytes]:
    """
    Generates a new Ed25519 private/public keypair and saves them in PEM format.
    """
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Serialize private key to PEM
    from cryptography.hazmat.primitives import serialization
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Serialize public key to PEM
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Ensure parent directories exist
    os.makedirs(os.path.dirname(os.path.abspath(private_path)), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(public_path)), exist_ok=True)

    # Save to files with strict permission flags
    with open(private_path, "wb") as f_priv:
        f_priv.write(private_pem)
    # Restrict permissions of the private key to owner-only read/write (0600)
    os.chmod(private_path, 0o600)

    with open(public_path, "wb") as f_pub:
        f_pub.write(public_pem)

    return private_pem, public_pem

def load_private_key(private_path: str) -> ed25519.Ed25519PrivateKey:
    """Loads an Ed25519 private key from PEM format."""
    from cryptography.hazmat.primitives import serialization
    with open(private_path, "rb") as f:
        private_pem = f.read()
    return serialization.load_pem_private_key(private_pem, password=None)

def load_public_key(public_path: str) -> ed25519.Ed25519PublicKey:
    """Loads an Ed25519 public key from PEM format."""
    from cryptography.hazmat.primitives import serialization
    with open(public_path, "rb") as f:
        public_pem = f.read()
    return serialization.load_pem_public_key(public_pem)

def get_deterministic_bytes(payload: Dict[str, Any]) -> bytes:
    """
    Serializes a dictionary deterministically by sorting keys, 
    stripping whitespace, and converting to compact UTF-8 format.
    """
    # Exclude any existing signature metadata from serialization to avoid self-referential signature mismatches
    cleansed_payload = {k: v for k, v in payload.items() if k not in ["signature", "signer_id"]}
    serialized_str = json.dumps(cleansed_payload, sort_keys=True, separators=(",", ":"))
    return serialized_str.encode("utf-8")

def sign_payload(payload: Dict[str, Any], private_key_path: str, signer_id: str = "Conductor") -> Dict[str, Any]:
    """
    Signs a JSON payload using an Ed25519 private key and appends the signature metadata.
    """
    private_key = load_private_key(private_key_path)
    data_bytes = get_deterministic_bytes(payload)
    signature_bytes = private_key.sign(data_bytes)
    
    # Store signature in hex format (128 characters)
    signed_payload = payload.copy()
    signed_payload["signer_id"] = signer_id
    signed_payload["signature"] = signature_bytes.hex()
    return signed_payload

def verify_payload_signature(payload: Dict[str, Any], public_key_path: str) -> bool:
    """
    Verifies the Ed25519 cryptographic signature of a payload.
    Returns True if valid, raises ValueError or returns False on failure.
    """
    if "signature" not in payload:
        raise ValueError("Integrity Failure: Missing signature envelope in packet frame.")
    
    signature_hex = payload["signature"]
    signature_bytes = bytes.fromhex(signature_hex)
    
    # Reload public key and verify deterministic representation of remaining data
    public_key = load_public_key(public_key_path)
    data_bytes = get_deterministic_bytes(payload)
    
    try:
        public_key.verify(signature_bytes, data_bytes)
        return True
    except InvalidSignature:
        return False

def main():
    parser = argparse.ArgumentParser(description="XORAS::OS — Cryptographic Thought and Payload Signer Gate")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--generate-keys", action="store_true", help="Generate secure Ed25519 private/public keypair.")
    group.add_argument("--sign", type=str, help="Absolute path to target JSON file containing the payload to sign.")
    group.add_argument("--verify", type=str, help="Absolute path to signed JSON file to verify.")

    parser.add_argument("--private-key", type=str, default=DEFAULT_PRIVATE_KEY_PATH, help="Path to private key PEM.")
    parser.add_argument("--public-key", type=str, default=DEFAULT_PUBLIC_KEY_PATH, help="Path to public key PEM.")
    parser.add_argument("--signer-id", type=str, default="Conductor", help="Identity identifier for the signing agent.")
    parser.add_argument("--output", type=str, help="Optional output path to write signed/verified results.")

    args = parser.parse_args()

    # --- ACTION: KEY GENERATION ---
    if args.generate_keys:
        try:
            generate_key_pair(args.private_key, args.public_key)
            print(json.dumps({
                "status": "SUCCESS",
                "message": "Secure Ed25519 keypair successfully generated and saved.",
                "private_key_path": args.private_key,
                "public_key_path": args.public_key
            }, indent=2))
            sys.exit(0)
        except Exception as e:
            print(json.dumps({"status": "FAILED", "error": f"Failed to generate keys: {str(e)}"}, indent=2))
            sys.exit(1)

    # --- ACTION: SIGN PAYLOAD ---
    elif args.sign:
        if not os.path.exists(args.sign):
            print(json.dumps({"status": "FAILED", "error": f"File not found: {args.sign}"}, indent=2))
            sys.exit(1)
        if not os.path.exists(args.private_key):
            print(json.dumps({"status": "FAILED", "error": f"Private key not found: {args.private_key}. Run with --generate-keys first."}, indent=2))
            sys.exit(1)
            
        try:
            with open(args.sign, "r") as f:
                payload = json.load(f)
            
            signed = sign_payload(payload, args.private_key, args.signer_id)
            
            # Write to output file or print
            if args.output:
                with open(args.output, "w") as out_f:
                    json.dump(signed, out_f, indent=2)
                print(json.dumps({"status": "SUCCESS", "message": f"Payload successfully signed and saved to {args.output}"}, indent=2))
            else:
                print(json.dumps(signed, indent=2))
            sys.exit(0)
        except Exception as e:
            print(json.dumps({"status": "FAILED", "error": f"Failed to sign payload: {str(e)}"}, indent=2))
            sys.exit(1)

    # --- ACTION: VERIFY SIGNATURE ---
    elif args.verify:
        if not os.path.exists(args.verify):
            print(json.dumps({"status": "FAILED", "error": f"File not found: {args.verify}"}, indent=2))
            sys.exit(1)
        if not os.path.exists(args.public_key):
            print(json.dumps({"status": "FAILED", "error": f"Public key not found: {args.public_key}"}, indent=2))
            sys.exit(1)

        try:
            with open(args.verify, "r") as f:
                payload = json.load(f)
            
            is_valid = verify_payload_signature(payload, args.public_key)
            if is_valid:
                print(json.dumps({
                    "status": "SUCCESS",
                    "message": "Cryptographic payload signature VERIFIED. Integrity intact.",
                    "signer_id": payload.get("signer_id", "Unknown")
                }, indent=2))
                sys.exit(0)
            else:
                print(json.dumps({
                    "status": "REJECTED",
                    "error": "Cryptographic payload signature MISMATCH. Dropping packet frame."
                }, indent=2))
                sys.exit(1)
        except Exception as e:
            print(json.dumps({"status": "FAILED", "error": f"Verification error: {str(e)}"}, indent=2))
            sys.exit(1)

if __name__ == "__main__":
    main()
