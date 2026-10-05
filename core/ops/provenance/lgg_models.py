# Minimal Living Goal Graph (MLGG) models
"""
Data models and helper functions for the Minimal Living Goal Graph.
These are thin wrappers around the ContextLineageEngine to store
GoalNode, DecisionNode, and EvidenceNode entries in the provenance DAG.
"""

import time
import hashlib
from dataclasses import dataclass
from typing import Dict, Any

from .context_lineage_dag_engine import ContextLineageEngine

engine = ContextLineageEngine()

def _hash(data: str) -> str:
    """Convenient SHA‑256 hash helper."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

@dataclass
class GoalNode:
    title: str
    parent_hash: str
    persona_lock_hash: str
    timestamp: float = time.time()
    node_id: str = None

    def commit(self) -> Dict[str, Any]:
        payload = {
            "title": self.title,
            "persona_lock_hash": self.persona_lock_hash,
            "timestamp": self.timestamp,
        }
        result = engine.commit_step(
            session_id="lgg",
            agent_id="maxx",
            step_type="GoalNode",
            payload=payload,
            parent_hash=self.parent_hash,
        )
        self.node_id = result["node_id"]
        return result

@dataclass
class DecisionNode:
    action_desc: str
    parent_hash: str
    output_hash: str = ""
    timestamp: float = time.time()
    node_id: str = None

    def commit(self) -> Dict[str, Any]:
        payload = {
            "action_desc": self.action_desc,
            "output_hash": self.output_hash,
            "timestamp": self.timestamp,
        }
        result = engine.commit_step(
            session_id="lgg",
            agent_id="maxx",
            step_type="DecisionNode",
            payload=payload,
            parent_hash=self.parent_hash,
        )
        self.node_id = result["node_id"]
        self.output_hash = _hash(self.action_desc) if not self.output_hash else self.output_hash
        return result

@dataclass
class EvidenceNode:
    file_path: str
    linked_decision_hash: str
    timestamp: float = time.time()
    node_id: str = None

    def commit(self) -> Dict[str, Any]:
        # Read file bytes and compute hash
        with open(self.file_path, "rb") as f:
            content = f.read()
        content_hash = _hash(content.decode('utf-8', errors='ignore'))
        payload = {
            "file_path": self.file_path,
            "content_hash": content_hash,
            "linked_decision_hash": self.linked_decision_hash,
            "timestamp": self.timestamp,
        }
        result = engine.commit_step(
            session_id="lgg",
            agent_id="maxx",
            step_type="EvidenceNode",
            payload=payload,
            parent_hash=self.linked_decision_hash,
        )
        self.node_id = result["node_id"]
        return result

# Helper to perform the lightweight consistency check for a new goal
def check_goal_consistency(persona_lock_hash: str, latest_decision_hash: str, expected_agg: str) -> bool:
    agg = _hash(persona_lock_hash + latest_decision_hash)
    return agg == expected_agg
