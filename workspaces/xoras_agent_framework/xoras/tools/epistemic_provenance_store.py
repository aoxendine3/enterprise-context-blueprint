"""
=============================================================================
XORAS HIGH-ASSURANCE EPISTEMIC PROVENANCE STORE TOOL
Path: workspaces/xoras_agent_framework/xoras/tools/epistemic_provenance_store.py
Standards: NIST SP 800-53 Rev. 5 (SI-7 Software/Information Integrity)
Capabilities: Hash-Chained Knowledge Entries, Ethical Alignment Filtering,
Immutable Fact Retention, Cryptographic State Validation.
=============================================================================
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class KnowledgeEntry:
    entry_id: str
    author_agent: str
    assertion_text: str
    ethical_alignment_score: float  # [0.0, 1.0]
    parent_entry_hash: str
    entry_hash: str
    timestamp_epoch_ms: int


class EpistemicProvenanceStore:
    """
    Append-only epistemic truth store maintaining cryptographic parent linkage
    and ethical alignment scoring for every asserted state or fact.
    """
    SCHEMA_VERSION = "xoras.epistemic_provenance.v1"
    MIN_ETHICAL_SCORE_THRESHOLD = 0.80  # Facts must meet biblical/moral alignment floor

    def __init__(self) -> None:
        self._chain: List[KnowledgeEntry] = []
        self._genesis_hash = hashlib.sha256(b"XORAS_GENESIS_TRUTH_2026").hexdigest()

    def commit_assertion(
        self,
        author_agent: str,
        assertion_text: str,
        ethical_alignment_score: float,
    ) -> Tuple[bool, Optional[KnowledgeEntry], str]:
        """Commit an assertion to the ledger after validating ethical score and hash linkage."""
        if ethical_alignment_score < self.MIN_ETHICAL_SCORE_THRESHOLD:
            return False, None, f"ETHICAL_ALIGNMENT_REJECTED: Score {ethical_alignment_score} < {self.MIN_ETHICAL_SCORE_THRESHOLD}"

        if not assertion_text.strip():
            return False, None, "EMPTY_ASSERTION_REJECTED"

        parent_hash = self._chain[-1].entry_hash if self._chain else self._genesis_hash
        ts_ms = int(time.time() * 1000)
        entry_id = f"KNOW_{len(self._chain) + 1:06d}"

        # Canonical hash computation
        envelope = f"{entry_id}:{author_agent}:{assertion_text}:{ethical_alignment_score}:{parent_hash}:{ts_ms}"
        entry_hash = hashlib.sha256(envelope.encode("utf-8")).hexdigest()

        entry = KnowledgeEntry(
            entry_id=entry_id,
            author_agent=author_agent,
            assertion_text=assertion_text,
            ethical_alignment_score=round(ethical_alignment_score, 4),
            parent_entry_hash=parent_hash,
            entry_hash=entry_hash,
            timestamp_epoch_ms=ts_ms,
        )

        self._chain.append(entry)
        return True, entry, "COMMITTED"

    def verify_chain_integrity(self) -> Tuple[bool, int, str]:
        """Verify the full hash chain from genesis to head."""
        if not self._chain:
            return True, 0, "EMPTY_CHAIN_VALID"

        expected_parent = self._genesis_hash
        for idx, entry in enumerate(self._chain):
            if entry.parent_entry_hash != expected_parent:
                return False, idx, f"BROKEN_PARENT_LINK at index {idx}"

            envelope = (
                f"{entry.entry_id}:{entry.author_agent}:{entry.assertion_text}:"
                f"{entry.ethical_alignment_score}:{entry.parent_entry_hash}:{entry.timestamp_epoch_ms}"
            )
            computed_hash = hashlib.sha256(envelope.encode("utf-8")).hexdigest()
            if computed_hash != entry.entry_hash:
                return False, idx, f"HASH_TAMPERING_DETECTED at index {idx}"

            expected_parent = entry.entry_hash

        return True, len(self._chain), "CHAIN_INTACT"

    def query_facts(self, keyword: str) -> List[Dict[str, Any]]:
        """Query committed facts matching keyword."""
        kw = keyword.lower()
        return [
            asdict(entry)
            for entry in self._chain
            if kw in entry.assertion_text.lower() or kw in entry.author_agent.lower()
        ]
