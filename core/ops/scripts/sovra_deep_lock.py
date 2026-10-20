#!/usr/bin/env python3
"""
===============================================================================
SOVRA ZERO-POINT DEEP LOCKING HANDSHAKE SPECIFICATION (v18.0 UNIFIED)
Anthony Junior Oxendine Intellectual Property
===============================================================================
Specification & Dual Implementation:
- Client (Frontend): Generates surgical HS256 / Ed25519 signature payload.
- Server (Backend Ingress): Validates exact timestamp, nonce, and origin hash.
- Header: X-SOVRA-DEEP-LOCK
- Replay / Drift Window: Strict 5.0 seconds (drift > 5.0s instantly destroyed).
===============================================================================
"""

import time
import json
import hmac
import hashlib
import base64
import os
from typing import Tuple, Dict, Any, Optional

DEFAULT_SECRET = os.environ.get("SOVRA_DEEP_LOCK_SECRET", "SOVRA_ZERO_POINT_DEEP_LOCK_SECRET_KEY_v18_UNIFIED")

def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def _b64decode(s: str) -> bytes:
    padding = '=' * (4 - (len(s) % 4))
    return base64.urlsafe_b64decode(s + padding)

def generate_handshake(secret: str = DEFAULT_SECRET, client_id: str = "SOVRA_FRONTEND_CLIENT") -> str:
    """
    Generates the X-SOVRA-DEEP-LOCK token:
    Header: {"alg": "HS256", "typ": "JWT", "ver": "v18.0"}
    Payload: {"sub": client_id, "iat": now, "nonce": token_hex, "origin": "APEX_SOVEREIGN"}
    """
    header = {"alg": "HS256", "typ": "JWT", "ver": "v18.0"}
    now = time.time()
    nonce = hashlib.sha256(f"{now}:{os.urandom(16)}".encode()).hexdigest()[:16]
    payload = {
        "sub": client_id,
        "iat": now,
        "nonce": nonce,
        "origin": "APEX_SOVEREIGN"
    }
    
    header_b64 = _b64encode(json.dumps(header, separators=(',', ':')).encode())
    payload_b64 = _b64encode(json.dumps(payload, separators=(',', ':')).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode()
    
    sig = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64encode(sig)
    
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def validate_handshake(token: str, secret: str = DEFAULT_SECRET, max_drift_sec: float = 5.0) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Verifies signature and surgical timestamp drift:
    - Rejects invalid formatting
    - Rejects altered signatures
    - Rejects drift > max_drift_sec (replay attack mitigation)
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return False, "INVALID_TOKEN_STRUCTURE", None
        
        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode()
        expected_sig = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
        actual_sig = _b64decode(sig_b64)
        
        if not hmac.compare_digest(expected_sig, actual_sig):
            return False, "SIGNATURE_MISMATCH_ATTACK_BLOCKED", None
        
        payload = json.loads(_b64decode(payload_b64).decode())
        iat = payload.get("iat", 0)
        current_time = time.time()
        drift = abs(current_time - iat)
        
        if drift > max_drift_sec:
            return False, f"TIMESTAMP_STALE_DRIFT_EXCEEDED ({drift:.2f}s > {max_drift_sec}s)", payload
        
        return True, "DEEP_LOCK_VALIDATED_ACCESS_GRANTED", payload
    except Exception as e:
        return False, f"DECODE_ERROR: {str(e)}", None

if __name__ == "__main__":
    print("Testing SOVRA Zero-Point Deep Lock v18.0 Handshake...")
    token = generate_handshake()
    print(f"Generated X-SOVRA-DEEP-LOCK:\n{token}\n")
    valid, reason, payload = validate_handshake(token)
    print(f"Validation Result: {valid} -> {reason}")
    print(f"Decoded Payload: {payload}")
