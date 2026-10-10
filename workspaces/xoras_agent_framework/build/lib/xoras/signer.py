"""
XORAS Systems LLC — Cryptographic Evidence & Trace Signer
Generates Ed25519 / HMAC SHA-256 verifiable execution receipts (xoras.evidence.v1).
"""

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional

@dataclass
class EvidenceReceipt:
    version: str
    timestamp: float
    organization: str
    agent_id: str
    action: str
    payload_hash: str
    status: str
    signature: str

class CryptographicSigner:
    def __init__(self, secret_key: Optional[bytes] = None, ed25519_private_bytes: Optional[bytes] = None):
        if secret_key:
            self.secret_key = secret_key
        else:
            self.secret_key = hashlib.sha256(b"XORAS_SYSTEMS_LLC_DEFAULT_AGENT_HMAC_KEY_2026").digest()
            
        # Ed25519 Asymmetric Key Pair
        try:
            from cryptography.hazmat.primitives.asymmetric import ed25519
            if ed25519_private_bytes and len(ed25519_private_bytes) == 32:
                self.ed25519_private_key = ed25519.Ed25519PrivateKey.from_private_bytes(ed25519_private_bytes)
            else:
                self.ed25519_private_key = ed25519.Ed25519PrivateKey.generate()
            self.ed25519_public_key = self.ed25519_private_key.public_key()
            self.has_ed25519 = True
        except ImportError:
            self.has_ed25519 = False

    def compute_hash(self, payload: Any) -> str:
        """Computes deterministic SHA-256 hash of JSON payload."""
        serialized = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    def sign_receipt(self, agent_id: str, action: str, payload: Dict[str, Any], status: str) -> EvidenceReceipt:
        """Signs an operational trace payload and generates an immutable receipt with Ed25519 & HMAC."""
        ts = time.time()
        payload_hash = self.compute_hash(payload)
        
        # Message envelope for signing
        envelope = f"XORAS_V1|{ts:.6f}|{agent_id}|{action}|{payload_hash}|{status}".encode("utf-8")
        
        if self.has_ed25519:
            sig_bytes = self.ed25519_private_key.sign(envelope)
            signature_b64 = f"ed25519_{base64.b64encode(sig_bytes).decode('utf-8')}"
        else:
            sig_bytes = hmac.new(self.secret_key, envelope, hashlib.sha256).digest()
            signature_b64 = f"hmac_{base64.b64encode(sig_bytes).decode('utf-8')}"

        return EvidenceReceipt(
            version="xoras.evidence.v1",
            timestamp=ts,
            organization="XORAS Systems LLC",
            agent_id=agent_id,
            action=action,
            payload_hash=payload_hash,
            status=status,
            signature=signature_b64
        )

    def verify_receipt(self, receipt: EvidenceReceipt) -> bool:
        """Verifies the mathematical signature of an evidence receipt using Ed25519 or HMAC."""
        envelope = f"XORAS_V1|{receipt.timestamp:.6f}|{receipt.agent_id}|{receipt.action}|{receipt.payload_hash}|{receipt.status}".encode("utf-8")
        
        if receipt.signature.startswith("ed25519_") and self.has_ed25519:
            raw_sig = base64.b64decode(receipt.signature[8:].encode("utf-8"))
            try:
                self.ed25519_public_key.verify(raw_sig, envelope)
                return True
            except Exception:
                return False
        elif receipt.signature.startswith("hmac_"):
            expected_sig = hmac.new(self.secret_key, envelope, hashlib.sha256).digest()
            actual_sig = base64.b64decode(receipt.signature[5:].encode("utf-8"))
            return hmac.compare_digest(expected_sig, actual_sig)
        else:
            # Fallback legacy signature match
            expected_sig = hmac.new(self.secret_key, envelope, hashlib.sha256).digest()
            actual_sig = base64.b64decode(receipt.signature.encode("utf-8"))
            return hmac.compare_digest(expected_sig, actual_sig)
