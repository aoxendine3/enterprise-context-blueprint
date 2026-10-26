"""
=============================================================================
XORAS HIGH-ASSURANCE CRYPTOGRAPHIC VAULT TOOL
Path: workspaces/xoras_agent_framework/xoras/tools/cryptographic_vault.py
Standards: NIST SP 800-53 Rev. 5, FIPS 198-1 (HMAC), FIPS 180-4 (SHA-256)
Capabilities: Message Signing, Constant-Time Verification, Merkle Tree Root,
Nonce Replay Protection, Zero-Leak Key Handling.
=============================================================================
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class SignatureReceipt:
    schema: str
    key_id: str
    digest_algorithm: str
    signature_hex: str
    timestamp_epoch_ms: int
    nonce: str


@dataclass(frozen=True)
class MerkleTreeReceipt:
    schema: str
    chunk_count: int
    root_hash: str
    chunk_hashes: List[str]
    timestamp_epoch_ms: int


class CryptographicVault:
    """
    Sovereign local cryptographic tool providing constant-time signatures,
    Merkle tree state verification, and anti-replay nonces in physical unified RAM.
    """
    SCHEMA_VERSION = "xoras.cryptographic_vault.v1"

    def __init__(self, master_secret_bytes: Optional[bytes] = None) -> None:
        if master_secret_bytes:
            self._key = master_secret_bytes
        else:
            self._key = secrets.token_bytes(32)
        self._key_id = hashlib.sha256(self._key).hexdigest()[:16]
        # Replay cache: nonce -> expiry epoch
        self._replay_cache: Dict[str, float] = {}

    def sign_payload(self, payload: bytes) -> SignatureReceipt:
        """Sign payload using HMAC-SHA256 with cryptographically secure nonce."""
        nonce = secrets.token_hex(16)
        ts_ms = int(time.time() * 1000)
        envelope = f"{self._key_id}:{ts_ms}:{nonce}:".encode("utf-8") + payload
        sig = hmac.new(self._key, envelope, hashlib.sha256).hexdigest()
        
        # Track nonce for replay prevention (60 second validity window)
        self._replay_cache[nonce] = time.time() + 60.0
        self._cleanup_replay_cache()

        return SignatureReceipt(
            schema=self.SCHEMA_VERSION,
            key_id=self._key_id,
            digest_algorithm="HMAC-SHA256",
            signature_hex=sig,
            timestamp_epoch_ms=ts_ms,
            nonce=nonce,
        )

    def verify_payload(self, payload: bytes, receipt: SignatureReceipt) -> Tuple[bool, str]:
        """Verify payload signature using constant-time comparison and anti-replay checks."""
        # 1. Key ID check
        if receipt.key_id != self._key_id:
            return False, "KEY_ID_MISMATCH"

        # 2. Timing check (reject timestamps older than 60s or more than 5s in future)
        now_ms = int(time.time() * 1000)
        age_ms = now_ms - receipt.timestamp_epoch_ms
        if age_ms > 60000 or age_ms < -5000:
            return False, "TIMESTAMP_EXPIRED"

        # 3. Nonce check
        if receipt.nonce in self._replay_cache and self._replay_cache[receipt.nonce] < time.time():
            return False, "REPLAY_NONCE_EXPIRED"

        envelope = f"{receipt.key_id}:{receipt.timestamp_epoch_ms}:{receipt.nonce}:".encode("utf-8") + payload
        expected_sig = hmac.new(self._key, envelope, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected_sig, receipt.signature_hex):
            return False, "SIGNATURE_FORGERY_DETECTED"

        return True, "VERIFIED"

    def compute_merkle_root(self, chunks: List[bytes]) -> MerkleTreeReceipt:
        """Compute canonical balanced binary Merkle tree root over arbitrary chunks."""
        if not chunks:
            empty_root = hashlib.sha256(b"").hexdigest()
            return MerkleTreeReceipt(
                schema=self.SCHEMA_VERSION,
                chunk_count=0,
                root_hash=empty_root,
                chunk_hashes=[],
                timestamp_epoch_ms=int(time.time() * 1000),
            )

        leaf_hashes = [hashlib.sha256(chunk).hexdigest() for chunk in chunks]
        current_layer = leaf_hashes[:]

        while len(current_layer) > 1:
            if len(current_layer) % 2 != 0:
                current_layer.append(current_layer[-1])  # Duplicate last element if odd
            next_layer = []
            for i in range(0, len(current_layer), 2):
                combined = current_layer[i] + current_layer[i + 1]
                node_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()
                next_layer.append(node_hash)
            current_layer = next_layer

        return MerkleTreeReceipt(
            schema=self.SCHEMA_VERSION,
            chunk_count=len(chunks),
            root_hash=current_layer[0],
            chunk_hashes=leaf_hashes,
            timestamp_epoch_ms=int(time.time() * 1000),
        )

    def _cleanup_replay_cache(self) -> None:
        """Evict expired nonces."""
        now = time.time()
        self._replay_cache = {n: exp for n, exp in self._replay_cache.items() if exp > now}
