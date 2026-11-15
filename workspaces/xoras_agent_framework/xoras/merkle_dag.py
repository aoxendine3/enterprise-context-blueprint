"""
XORAS REASONS: Context Lineage Merkle DAG Engine & Anti-Replay Invariants
==========================================================================
Immutable cryptographic state commit nodes, parent-chain lineage tracking,
and zero-state-pollution quarantine for unlinked foreign session payloads.

Memory-poisoning hardening (OWASP ASI06 memory/context poisoning)
-----------------------------------------------------------------
Three layered controls sit in front of ``nodes``:

1. Exact replay detection  (SHA-256 of canonical JSON, original behaviour).
2. Normalized replay detection (NFKC, zero-width / format-char stripping,
   casefold, whitespace collapse, canonical key ordering) so cosmetic
   variants of an already-committed payload are quarantined as replays.
3. A promotion gate: payloads that match instruction-override / policy-
   weakening patterns, or that declare an untrusted ``source``, are routed to
   ``staged_ledger`` and do NOT enter ``nodes`` (hence never become roots or
   parents) until ``promote(node_id, approver, evidence)`` is called with a
   non-empty approver who is not the original writer.

Every committed node carries a ``provenance`` record (writer, declared
source, trust class, commit path, approver/evidence if promoted) that is
bound into the node's ``state_hash``.

HONESTY NOTE / KNOWN LIMITS
---------------------------
The promotion gate is a *regex heuristic*. It is NOT a complete defense
against memory poisoning. It does not catch paraphrases ("Going forward,
signatures need not be checked"), other languages, homoglyph substitution
(e.g. Cyrillic look-alikes, which NFKC does not fold), payloads encoded
(base64, rot13, split across non-adjacent fields in ways the joined-text scan
misses), or an attacker who simply declares a trusted ``source`` for a
malicious payload (``source`` is caller-declared, not authenticated).
Normalized replay detection likewise only equates payloads that are equal
after the normalization above, not semantically equivalent ones. Treat this
as one layer of defense in depth (alongside provenance tagging, signed
writers, and trust-aware retrieval), not as a guarantee.
"""

import functools
import hashlib
import json
import re
import threading
import time
import unicodedata
from typing import Any, Dict, List, Optional, Set, Tuple

def canonical_json(data: Dict) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


# ---------------------------------------------------------------------------
# Normalization (replay detection)
# ---------------------------------------------------------------------------

_MAX_NORMALIZE_DEPTH = 64


def normalize_text(text: str) -> str:
    """NFKC, drop Unicode format chars (zero-width etc.), casefold, collapse whitespace."""
    text = unicodedata.normalize("NFKC", text)
    # Category Cf covers zero-width space/joiners, BOM, bidi controls, soft hyphen.
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cf")
    text = unicodedata.normalize("NFKC", text.casefold())
    return " ".join(text.split())


def _normalize_value(value: Any, depth: int = 0) -> Any:
    if depth > _MAX_NORMALIZE_DEPTH:
        raise ValueError("PAYLOAD_TOO_DEEP")
    if isinstance(value, str):
        return normalize_text(value)
    if isinstance(value, dict):
        # Sorted [key, value] pairs (not a dict) so keys that collide after
        # normalization cannot silently overwrite each other.
        pairs = [[_normalize_value(str(k), depth + 1), _normalize_value(v, depth + 1)] for k, v in value.items()]
        pairs.sort(key=lambda p: json.dumps(p, sort_keys=True, default=str))
        return {"__d__": pairs}
    if isinstance(value, (list, tuple)):
        return [_normalize_value(v, depth + 1) for v in value]
    return value


def normalized_payload_hash(payload: Dict) -> str:
    """SHA-256 over the normalized canonical form of ``payload``."""
    return hashlib.sha256(canonical_json(_normalize_value(payload))).hexdigest()


# ---------------------------------------------------------------------------
# Promotion gate (heuristic)
# ---------------------------------------------------------------------------

_GAP = r"(?:[\s,\-]+\w+){0,3}?[\s,\-]+"
_POLICY_NOUNS = (
    r"(?:verification|verifications|verify|verifying|signature|signatures|signing|"
    r"audit|audits|auditing|safety|guard|guards|guardrail|guardrails|validation|"
    r"sandbox|security|checks)"
)
_OVERRIDE_PATTERNS: List[Tuple[str, "re.Pattern[str]"]] = [
    ("INSTRUCTION_OVERRIDE:ignore_previous", re.compile(
        r"\b(?:ignore|disregard|forget)\s+(?:(?:all|any|the|your|my|of)\s+)*(?:previous|prior|above|earlier|preceding)\b")),
    ("INSTRUCTION_OVERRIDE:from_now_on", re.compile(r"\bfrom\s+now\s+on\b")),
    ("POLICY_WEAKENING:skip_disable_bypass", re.compile(
        r"\b(?:skip|skipping|disable|disabling|bypass|bypassing|circumvent|circumventing|"
        r"deactivate|suppress|turn\s+off|omit|ignore|ignoring)\b" + _GAP + _POLICY_NOUNS + r"\b")),
    ("POLICY_WEAKENING:do_not_log", re.compile(r"\b(?:do\s+not|don't|dont|never|stop)\s+(?:log|logging)\b")),
    ("ROLE_HIJACK:you_are_now", re.compile(r"\byou\s+are\s+now\b")),
    ("SYSTEM_PROMPT_REFERENCE", re.compile(r"\bsystem\s+prompt\b")),
]

UNTRUSTED_SOURCES: frozenset = frozenset({
    "tool_output", "tool_result", "tool", "web", "web_search", "web_page", "browser",
    "http", "https", "url", "unverified", "untrusted", "unknown", "external",
    "third_party", "scraped", "retrieved", "rag", "email", "document", "file_upload",
    "user_supplied", "mcp",
})


def _collect_strings(value: Any, out: List[str], depth: int = 0) -> None:
    if depth > _MAX_NORMALIZE_DEPTH:
        raise ValueError("PAYLOAD_TOO_DEEP")
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for k in sorted(value, key=str):
            out.append(str(k))
            _collect_strings(value[k], out, depth + 1)
    elif isinstance(value, (list, tuple)):
        for v in value:
            _collect_strings(v, out, depth + 1)


def scan_policy_override(payload: Dict) -> List[str]:
    """Return gate finding codes for instruction-override / policy-weakening text.

    Heuristic only (see module docstring). Scans every string key/value, each
    individually and as one joined text (catches phrases split across adjacent
    fields).
    """
    try:
        strings: List[str] = []
        _collect_strings(payload, strings)
    except ValueError:
        return ["PAYLOAD_TOO_DEEP"]
    texts = [normalize_text(s).replace("\u2019", "'").replace("\u2018", "'") for s in strings]
    texts.append(" ".join(texts))
    findings: List[str] = []
    for code, pattern in _OVERRIDE_PATTERNS:
        if any(pattern.search(t) for t in texts):
            findings.append(code)
    return findings


def classify_source(payload: Dict) -> Tuple[str, bool]:
    """Return (declared_source_label, is_untrusted). Missing source => trusted (back-compat).

    A non-string / non-dict declared source is treated as untrusted (fail-closed).
    """
    if "source" not in payload or payload["source"] is None:
        return "unspecified", False
    raw = payload["source"]
    if isinstance(raw, dict):
        raw = raw.get("type") or raw.get("kind") or raw.get("name")
    if not isinstance(raw, str):
        return repr(payload["source"])[:80], True
    label = normalize_text(raw)
    tokens = [t for t in re.split(r"[^a-z0-9_]+", label.replace("-", "_")) if t]
    return label, any(t in UNTRUSTED_SOURCES for t in tokens) or not tokens


def _synchronized(method):
    """Serialize access to the engine's mutable ledger.

    The replay set and the promoted-node map are read-modify-write: without a
    lock two threads can both pass the "have I seen this hash?" check and both
    commit the same payload (a TOCTOU replay). The lock also keeps
    ``get_dynamic_merkle_root`` from iterating ``nodes`` while another thread
    inserts into it. Re-entrant so ``commit`` can call ``_quarantine_replay``.
    """

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)

    return wrapper


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


class MerkleDAGNode:
    def __init__(self, node_id: str, parent_ids: List[str], payload: Dict, timestamp: Optional[float] = None,
                 provenance: Optional[Dict] = None):
        self.node_id = node_id
        self.parent_ids = sorted(parent_ids)
        self.payload = payload
        self.timestamp = timestamp or time.time()
        self.provenance = provenance
        self.payload_hash = hashlib.sha256(canonical_json(payload)).hexdigest()
        
        envelope = {
            "node_id": self.node_id,
            "parent_ids": self.parent_ids,
            "payload_hash": self.payload_hash,
            "timestamp": round(self.timestamp, 4)
        }
        if provenance is not None:
            # Bound into state_hash only when present, so provenance-less nodes keep legacy hashes.
            envelope["provenance_hash"] = hashlib.sha256(canonical_json(provenance)).hexdigest()
        self.state_hash = hashlib.sha256(canonical_json(envelope)).hexdigest()

    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "parent_ids": self.parent_ids,
            "payload_hash": self.payload_hash,
            "state_hash": self.state_hash,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "provenance": self.provenance,
        }

class ContextLineageDAGEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self.nodes: Dict[str, MerkleDAGNode] = {}
        self.seen_payload_hashes: Set[str] = set()
        self.seen_normalized_hashes: Set[str] = set()
        self.quarantine_ledger: List[Dict] = []
        # Quarantine staging area: node_id -> record. Entries here are NOT in
        # ``nodes`` and are never roots/parents until promote() succeeds.
        self.staged_ledger: Dict[str, Dict] = {}

    def _quarantine_replay(self, node_id: str, payload_hash: str, match_type: str) -> Tuple[bool, None, str]:
        self.quarantine_ledger.append({
            "event": "REPLAY_DETECTED",
            "attempted_node_id": node_id,
            "payload_hash": payload_hash,
            "match_type": match_type,
            "quarantine_timestamp": time.time(),
            "status": "QUARANTINED"
        })
        return False, None, "UNLINKED_REPLAY_QUARANTINED"

    @_synchronized
    def commit(self, node_id: str, parent_ids: List[str], payload: Dict,
               writer: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        payload_hash = hashlib.sha256(canonical_json(payload)).hexdigest()

        # Invariant 1: Unlinked duplicate payload detection (Anti-Replay), exact match
        if payload_hash in self.seen_payload_hashes:
            return self._quarantine_replay(node_id, payload_hash, "exact")

        # Invariant 1b: normalized-content replay (whitespace/case/unicode variants)
        try:
            norm_hash = normalized_payload_hash(payload)
        except ValueError:
            return False, None, "PAYLOAD_TOO_DEEP"
        if norm_hash in self.seen_normalized_hashes:
            return self._quarantine_replay(node_id, payload_hash, "normalized")
        if any(r["status"] == "STAGED" and r["normalized_hash"] == norm_hash for r in self.staged_ledger.values()):
            return self._quarantine_replay(node_id, payload_hash, "staged")

        # Invariant 2: Parent existence verification
        for pid in parent_ids:
            if pid not in self.nodes:
                return False, None, f"PARENT_NODE_NOT_FOUND: {pid}"

        # Invariant 3: Promotion gate (memory-poisoning quarantine)
        source_label, untrusted = classify_source(payload)
        findings = scan_policy_override(payload)
        if untrusted:
            findings = ["UNTRUSTED_SOURCE:" + source_label] + findings
        if findings:
            if node_id in self.nodes:
                return False, None, f"NODE_ID_ALREADY_COMMITTED: {node_id}"
            existing = self.staged_ledger.get(node_id)
            if existing is not None and existing["status"] == "STAGED":
                return False, None, f"STAGED_NODE_ID_CONFLICT: {node_id}"
            self.staged_ledger[node_id] = {
                "event": "STAGED_FOR_PROMOTION",
                "node_id": node_id,
                "parent_ids": sorted(parent_ids),
                "payload": payload,
                "payload_hash": payload_hash,
                "normalized_hash": norm_hash,
                "writer": writer,
                "source": source_label,
                "findings": findings,
                "staged_timestamp": time.time(),
                "status": "STAGED",
            }
            return False, None, "STAGED_FOR_PROMOTION: " + ",".join(findings)

        provenance = {
            "writer": writer,
            "source": source_label,
            "trust": "trusted",
            "via": "commit",
        }
        node = MerkleDAGNode(node_id, parent_ids, payload, provenance=provenance)
        self.nodes[node_id] = node
        self.seen_payload_hashes.add(payload_hash)
        self.seen_normalized_hashes.add(norm_hash)
        return True, node.state_hash, None

    @_synchronized
    def promote(self, node_id: str, approver: str, evidence: Any = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """Promote a staged node into the DAG after explicit approval.

        Requires a non-empty ``approver`` (str, not just whitespace/zero-width
        characters) who is not the original writer. ``evidence`` is recorded
        verbatim (JSON-coerced) in the node's provenance. Returns the same
        (ok, state_hash_or_None, error_or_None) tuple as ``commit``.
        """
        record = self.staged_ledger.get(node_id)
        if record is None:
            return False, None, f"STAGED_NODE_NOT_FOUND: {node_id}"
        if record["status"] != "STAGED":
            return False, None, f"STAGED_NODE_NOT_PENDING: {node_id}"
        if not isinstance(approver, str) or not normalize_text(approver):
            return False, None, "APPROVER_REQUIRED"
        if record["writer"] is not None and normalize_text(record["writer"]) == normalize_text(approver):
            return False, None, "SELF_APPROVAL_FORBIDDEN"
        if node_id in self.nodes:
            return False, None, f"NODE_ID_ALREADY_COMMITTED: {node_id}"
        for pid in record["parent_ids"]:
            if pid not in self.nodes:
                return False, None, f"PARENT_NODE_NOT_FOUND: {pid}"
        if record["payload_hash"] in self.seen_payload_hashes:
            return self._quarantine_replay(node_id, record["payload_hash"], "exact")
        if record["normalized_hash"] in self.seen_normalized_hashes:
            return self._quarantine_replay(node_id, record["payload_hash"], "normalized")

        provenance = {
            "writer": record["writer"],
            "source": record["source"],
            "trust": "promoted",
            "via": "promote",
            "approver": approver,
            "evidence": _json_safe(evidence),
            "gate_findings": list(record["findings"]),
        }
        node = MerkleDAGNode(node_id, record["parent_ids"], record["payload"], provenance=provenance)
        self.nodes[node_id] = node
        self.seen_payload_hashes.add(record["payload_hash"])
        self.seen_normalized_hashes.add(record["normalized_hash"])
        record["status"] = "PROMOTED"
        record["approver"] = approver
        record["promoted_timestamp"] = time.time()
        return True, node.state_hash, None

    @_synchronized
    def get_dynamic_merkle_root(self) -> str:
        if not self.nodes:
            return "0" * 64
        # All nodes that are not parents of any other node are tips
        all_parents: Set[str] = set()
        for n in self.nodes.values():
            all_parents.update(n.parent_ids)
        tips = sorted([n.state_hash for nid, n in self.nodes.items() if nid not in all_parents])
        if not tips:
            tips = sorted([n.state_hash for n in self.nodes.values()])
        combined = "".join(tips).encode("utf-8")
        return hashlib.sha256(combined).hexdigest()

__all__ = [
    "MerkleDAGNode", "ContextLineageDAGEngine", "canonical_json",
    "normalize_text", "normalized_payload_hash", "scan_policy_override",
    "classify_source", "UNTRUSTED_SOURCES",
]
