#!/usr/bin/env python3
"""
=============================================================================
SOVRA ZERO-POINT DEEP LOCKING PROTOCOL (v18.0 UNIFIED STANDARD)
Proprietary Intellectual Property of Anthony Junior Oxendine
Cryptographically binds:
  1. Local Apple Silicon M4 SSOT Node
  2. Bare-Metal Windows x86 GPU Cluster (192.168.1.211)
  3. Cloud DAXX Conductor & Stage Egress
Locks out all unauthorized external extraction vectors and severance attacks.
=============================================================================
"""
import os
import sys
import json
import time
import hmac
import hashlib
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LOCK_SECRET_FILE = ROOT / "memory" / "vault" / "sovra_deep_lock.key"
LOCK_RECEIPTS_FILE = ROOT / "memory" / "context_scopes" / "deep_lock_receipts.jsonl"

LOCK_SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)
LOCK_RECEIPTS_FILE.parent.mkdir(parents=True, exist_ok=True)

# Generate or load sovereign master secret
def get_master_secret() -> bytes:
    if not LOCK_SECRET_FILE.exists():
        secret = hashlib.sha256(f"ANTHONY_OXENDINE_SOVRA_DEEP_LOCK_{time.time()}_{os.urandom(32)}".encode()).digest()
        LOCK_SECRET_FILE.write_bytes(secret)
        os.chmod(LOCK_SECRET_FILE, 0o600)
        return secret
    return LOCK_SECRET_FILE.read_bytes()

# Nonce replay cache: nonce -> expiry timestamp. Cleared via reset_nonce_cache().
_NONCE_CACHE: dict = {}
_USED_NONCES: set = set()

def reset_nonce_cache() -> None:
    """Clears the sovereign deep-lock nonce replay cache."""
    _NONCE_CACHE.clear()
    _USED_NONCES.clear()

def generate_handshake(origin: str = "MAC_M4_SSOT", target: str = "WINDOWS_GPU_NODE_192.168.1.211", metadata: dict = None, subject: str = "FRONTEND_BACKEND_DEEP_LOCK") -> str:
    """
    Generates surgical cryptographic handshake token (HS256 compliant)
    Valid for exactly 60 seconds to eliminate replay windows.

    `subject` defaults to the canonical deep-lock subject used by the
    cross-language verifier (workspaces/xmars-app/src/lib/auth/Handshake.ts),
    so a token minted in Python validates byte-identically in TypeScript.
    """
    secret = get_master_secret()
    now = time.time()
    
    header = {"alg": "HS256", "typ": "SOVRA-DEEP-LOCK", "ver": "v18.0_UNIFIED"}
    payload = {
        "iss": "SOVRA_ZERO_POINT",
        "sub": subject,
        "origin": origin,
        "target": target,
        "iat": now,
        "exp": now + 60.0,
        "nonce": os.urandom(16).hex(),
        "metadata": metadata or {}
    }
    
    h_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    msg = f"{h_b64}.{p_b64}".encode()
    
    sig = hmac.new(secret, msg, hashlib.sha256).digest()
    s_b64 = base64.urlsafe_b64encode(sig).decode().rstrip("=")
    
    token = f"{h_b64}.{p_b64}.{s_b64}"
    
    # Commit audit receipt
    receipt = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        "token_sig": s_b64[:16],
        "origin": origin,
        "target": target,
        "status": "SEALED_AND_ACTIVE"
    }
    with open(LOCK_RECEIPTS_FILE, "a", encoding="utf-8") as rf:
        rf.write(json.dumps(receipt) + "\n")
        
    _NONCE_CACHE[payload.get("nonce")] = now + 60.0
    return token

def validate_handshake(token: str, max_drift_seconds: float = 60.0, check_replay: bool = True) -> tuple[bool, str, dict]:
    secret = get_master_secret()
    parts = token.split(".")
    if len(parts) != 3:
        return False, "INVALID_TOKEN_STRUCTURE", {}
        
    h_b64, p_b64, s_b64 = parts
    msg = f"{h_b64}.{p_b64}".encode()
    expected_sig = hmac.new(secret, msg, hashlib.sha256).digest()
    expected_s_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip("=")
    
    if not hmac.compare_digest(s_b64, expected_s_b64):
        return False, "SIGNATURE_CORRUPTED_OR_TAMPERED", {}
        
    try:
        pad = "=" * ((4 - len(p_b64) % 4) % 4)
        payload = json.loads(base64.urlsafe_b64decode((p_b64 + pad).encode()).decode())
    except Exception:
        return False, "MALFORMED_PAYLOAD", {}
        
    now = time.time()
    if now > payload.get("exp", 0):
        return False, "TOKEN_EXPIRED", payload
    if abs(now - payload.get("iat", 0)) > max_drift_seconds:
        return False, "EXCESSIVE_CLOCK_DRIFT", payload
        
    if check_replay:
        nonce = payload.get("nonce")
        if nonce in _USED_NONCES:
            return False, "NONCE_REPLAY_DETECTED", payload
        _USED_NONCES.add(nonce)
    _NONCE_CACHE[nonce] = now + 60.0 if nonce else _NONCE_CACHE.get(nonce, now + 60.0)
        
    return True, "DEEP_LOCK_VALIDATED_SEALED", payload

if __name__ == "__main__":
    t0 = time.time()
    token = generate_handshake(
        origin="MAC_M4_SSOT",
        target="WINDOWS_GPU_NODE_192.168.1.211",
        metadata={"scope_hash": "c19488d236eb841b", "port": 11434}
    )
    dt_gen = round((time.time() - t0) * 1000, 2)
    print("SOVRA Zero-Point Deep Lock Generated in", dt_gen, "ms")
    print("Token:", token[:32] + "..." + token[-16:])
    
    t1 = time.time()
    valid, reason, payload = validate_handshake(token)
    dt_val = round((time.time() - t1) * 1000, 2)
    print("Validation Verdict:", reason, "in", dt_val, "ms")
    print("Origin -> Target:", payload["origin"], "->", payload["target"])
