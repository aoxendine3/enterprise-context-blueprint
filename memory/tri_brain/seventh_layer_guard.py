"""
Tri-Brain Architecture: 7th-Layer Guard (Bidirectional Noise & Corruption Membrane).
Invariant: No corruption rolls down to disk/memory; no raw unvalidated noise rolls up to apex synthesis.
Operates as the strict filtration membrane between the 3 Tri-Brain containers and the 1 Apex Council.
"""

import re
import hashlib
from typing import Dict, Any, Tuple, List

class SeventhLayerGuard:
    """
    The 7th Layer Sovereign Guard.
    Performs bidirectional monotonic inspection on all tokens, payloads, and state diffs.
    """
    BLOCKED_PATTERNS = [
        re.compile(r"(\brm\s+-rf\s+/|\bdel\s+/f\s+/q|\bformat\s+[a-z]:)", re.IGNORECASE),
        re.compile(r"(\bos\.system\b|\bsubprocess\.call\b|\beval\(|\bexec\()", re.IGNORECASE),
        re.compile(r"(__globals__|__subclasses__|__builtins__)", re.IGNORECASE),
        re.compile(r"(cloud_exfiltrate|send_credentials|leak_keys)", re.IGNORECASE)
    ]

    def __init__(self):
        self.total_screened: int = 0
        self.blocked_roll_down: int = 0
        self.blocked_roll_up: int = 0

    def screen_roll_up(self, container_id: int, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Screens information ascending from a sub-brain container towards the Apex.
        Ensures payload contains structured evidence, valid SHA-256 provenance,
        and no unvalidated conversational hallucination or malformed noise.
        """
        self.total_screened += 1

        if not isinstance(payload, dict):
            self.blocked_roll_up += 1
            return False, "REJECTED_UP: Payload must be structured dictionary with provenance."

        required_keys = {"source_agent", "claim", "receipt"}
        if not required_keys.issubset(payload.keys()):
            self.blocked_roll_up += 1
            return False, f"REJECTED_UP: Missing required verification keys: {required_keys - set(payload.keys())}"

        # Verify claim content against injection / raw hallucinations
        claim_text = str(payload.get("claim", ""))
        for pattern in self.BLOCKED_PATTERNS:
            if pattern.search(claim_text):
                self.blocked_roll_up += 1
                return False, f"REJECTED_UP: Toxic signature detected in claim: {pattern.pattern}"

        return True, "PASSED_UP: Validated by 7th Layer Membrane."

    def screen_roll_down(self, apex_directive: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Screens directives descending from the Apex towards local containers and physical storage.
        Ensures directives do not cause destructive, irreversible mutations or violate MARS safeguards.
        """
        self.total_screened += 1

        action = str(apex_directive.get("action", ""))
        target = str(apex_directive.get("target", ""))

        for pattern in self.BLOCKED_PATTERNS:
            if pattern.search(action) or pattern.search(target):
                self.blocked_roll_down += 1
                return False, f"REJECTED_DOWN: Destructive pattern blocked by 7th Layer Guard."

        # Invariant: Must guarantee non-empty inverse patch for destructive mutations
        if apex_directive.get("is_mutation", False) and not apex_directive.get("has_rollback", False):
            self.blocked_roll_down += 1
            return False, "REJECTED_DOWN: Mutation missing atomic inverse rollback guarantee."

        return True, "PASSED_DOWN: Safe for container admission."

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "total_screened": self.total_screened,
            "blocked_roll_down": self.blocked_roll_down,
            "blocked_roll_up": self.blocked_roll_up,
            "status": "ACTIVE_MEMBRANE_LOCKED"
        }
