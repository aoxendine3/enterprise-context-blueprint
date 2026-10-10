"""
XORAS R&D Prototype 4: Bare-Metal Hardware Taint Lattice for AI Payloads (Fail-Closed Remediated)
Tags inbound bytes with candidate<T> (0xDEAD0000) taint flags and enforces HMAC anti-spoofing signature verification before decision<T> (0xBEAF0000) promotion.
Remediates BBQ-03 (False positive DoS), BBQ-04 (Indirect sink bypass), and BBQ-05 (Taint flag forgery).
"""

import re
import hmac
import hashlib
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional

class TaintState(Enum):
    CANDIDATE_TAINTED = 0xDEAD0000
    DECISION_VERIFIED = 0xBEAF0000
    BLOCKED_MALICIOUS = 0xFFFFFFFF

@dataclass
class TaintPromotionResult:
    is_promoted: bool
    taint_state: TaintState
    memory_tag: str
    rejection_reason: Optional[str] = None

class HardwareTaintLattice:
    def __init__(self, hmac_secret: bytes = b"xoras_lattice_hardware_key_2026"):
        self.hmac_secret = hmac_secret
        self.prohibited_tokens = [
            r"\beval\b", r"\bexec\b", r"\bsystem\b", r"\bpopen\b", r"drop\s+table",
            r"__import__", r"importlib", r"ctypes", r"getattr", r"setattr"
        ]

    def _sign_packet(self, raw_payload: str, taint_flag: int) -> str:
        msg = f"{raw_payload}:{taint_flag}".encode('utf-8')
        return hmac.new(self.hmac_secret, msg, hashlib.sha256).hexdigest()

    def ingest_candidate(self, raw_input: str, source_id: str) -> Dict[str, Any]:
        taint_flag = TaintState.CANDIDATE_TAINTED.value
        sig = self._sign_packet(raw_input, taint_flag)
        return {
            "source_id": source_id,
            "raw_payload": raw_input,
            "taint_flag": taint_flag,
            "taint_label": "candidate<T>",
            "hmac_signature": sig,
            "memory_tag": f"0xDEAD_{sig[:8].upper()}"
        }

    def evaluate_gate_promotion(self, candidate_packet: Dict[str, Any]) -> TaintPromotionResult:
        payload = str(candidate_packet.get("raw_payload", ""))
        taint_flag = candidate_packet.get("taint_flag")
        sig = candidate_packet.get("hmac_signature", "")

        # 1. Anti-Spoofing & Signature Verification
        expected_sig = self._sign_packet(payload, TaintState.CANDIDATE_TAINTED.value)
        if not hmac.compare_digest(sig, expected_sig) or taint_flag != TaintState.CANDIDATE_TAINTED.value:
            return TaintPromotionResult(
                is_promoted=False,
                taint_state=TaintState.BLOCKED_MALICIOUS,
                memory_tag="0xFFFF_BLOCKED",
                rejection_reason="Taint Lattice Error: Unsigned or forged candidate packet detected"
            )

        # 2. Token Boundary Prohibited Execution Sinks Check
        for pat in self.prohibited_tokens:
            if re.search(pat, payload, re.IGNORECASE):
                return TaintPromotionResult(
                    is_promoted=False,
                    taint_state=TaintState.BLOCKED_MALICIOUS,
                    memory_tag="0xFFFF_BLOCKED",
                    rejection_reason=f"Taint Lattice Gate Rejection: Prohibited token match '{pat}'"
                )

        promoted_sig = self._sign_packet(payload, TaintState.DECISION_VERIFIED.value)
        return TaintPromotionResult(
            is_promoted=True,
            taint_state=TaintState.DECISION_VERIFIED,
            memory_tag=f"0xBEAF_{promoted_sig[:8].upper()}",
            rejection_reason=None
        )
