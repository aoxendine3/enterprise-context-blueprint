"""
REASONS: Context Lineage Merkle DAG Engine & Anti-Replay Invariants
===================================================================
Provides immutable cryptographic state commit nodes, parent-chain lineage tracking,
and zero-state-pollution quarantine for unlinked foreign session payloads.
"""

import hashlib
import json
import time
from typing import Dict, List, Optional, Set, Tuple


def canonical_json(data: Dict) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


class MerkleDAGNode:
    def __init__(self, node_id: str, parent_ids: List[str], payload: Dict, timestamp: Optional[float] = None):
        self.node_id = node_id
        self.parent_ids = sorted(parent_ids)
        self.payload = payload
        self.timestamp = timestamp or time.time()
        self.payload_hash = hashlib.sha256(canonical_json(payload)).hexdigest()
        
        envelope = {
            "node_id": self.node_id,
            "parent_ids": self.parent_ids,
            "payload_hash": self.payload_hash,
            "timestamp": round(self.timestamp, 4)
        }
        self.state_hash = hashlib.sha256(canonical_json(envelope)).hexdigest()

    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "parent_ids": self.parent_ids,
            "payload_hash": self.payload_hash,
            "state_hash": self.state_hash,
            "timestamp": self.timestamp,
            "payload": self.payload
        }


class ContextLineageDAGEngine:
    def __init__(self):
        self.nodes: Dict[str, MerkleDAGNode] = {}
        self.seen_payload_hashes: Set[str] = set()
        self.quarantine_ledger: List[Dict] = []

    def commit(self, node_id: str, parent_ids: List[str], payload: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Commits a state node into the Merkle DAG.
        Enforces Anti-Replay Invariant & Parent Existence Invariant.
        """
        payload_hash = hashlib.sha256(canonical_json(payload)).hexdigest()

        # Invariant 1: Unlinked duplicate payload detection (Anti-Replay)
        if payload_hash in self.seen_payload_hashes:
            # Check if this exact node is being re-committed or foreign replayed
            quarantine_obj = {
                "type": "xoras.evidence.v1",
                "attack": "CROSS_SESSION_UNLINKED_REPLAY",
                "payload_hash": payload_hash,
                "node_id": node_id,
                "timestamp": time.time(),
                "disposition": "QUARANTINED"
            }
            self.quarantine_ledger.append(quarantine_obj)
            return False, None, f"Anti-Replay Invariant Triggered: payload {payload_hash[:12]} quarantined."

        # Invariant 2: Parent lineage continuity (except genesis)
        if parent_ids:
            for pid in parent_ids:
                if pid not in self.nodes:
                    return False, None, f"Broken Lineage: parent node {pid} does not exist in DAG."

        node = MerkleDAGNode(node_id, parent_ids, payload)
        self.nodes[node_id] = node
        self.seen_payload_hashes.add(payload_hash)
        return True, node.state_hash, None

    def compute_merkle_root(self) -> str:
        """
        Computes the global Merkle root over all active tips (nodes with no children).
        """
        if not self.nodes:
            return "0" * 64

        all_parents = set()
        for node in self.nodes.values():
            all_parents.update(node.parent_ids)

        tips = [n for nid, n in self.nodes.items() if nid not in all_parents]
        tip_hashes = sorted([n.state_hash for n in tips])

        combined = "".join(tip_hashes).encode("utf-8")
        return hashlib.sha256(combined).hexdigest()

    def verify_node_integrity(self, node_id: str) -> bool:
        if node_id not in self.nodes:
            return False
        node = self.nodes[node_id]
        current_payload_hash = hashlib.sha256(canonical_json(node.payload)).hexdigest()
        if current_payload_hash != node.payload_hash:
            return False
        envelope = {
            "node_id": node.node_id,
            "parent_ids": node.parent_ids,
            "payload_hash": current_payload_hash,
            "timestamp": round(node.timestamp, 4)
        }
        recomputed = hashlib.sha256(canonical_json(envelope)).hexdigest()
        return recomputed == node.state_hash
