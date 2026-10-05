#!/usr/bin/env python3
"""
===============================================================================
SOVEREIGN CONTEXT LINEAGE & EXECUTION PROVENANCE ENGINE (v1.2.0)
===============================================================================
Core Engine: Cryptographic Merkle-DAG Context Tracking & Lineage Verification.

Hardened with:
- Anti-Corruption: Full payload SHA-256 integrity verification against bit-flips.
- Anti-Replay: Monotonic sequence tracking, non-monotonic timestamp rejection,
  and cross-session duplicate node-id rejection.

Author: The Lead 9 Council / Xoras Systems
Date: 2026-09-30
===============================================================================
"""

import os
import sys
import json
import time
import hmac
import sqlite3
import hashlib
from typing import Dict, List, Optional, Tuple, Any

# Canonical DB Path
DB_DIR = os.path.expanduser("~/Desktop/SSOT_Agentic_Brain/.sovereign/provenance")
DB_PATH = os.path.join(DB_DIR, "lineage_dag.db")

def get_hmac_key() -> bytes:
    env_key = os.environ.get("XORAS_HARDWARE_HMAC_KEY")
    if env_key:
        return env_key.encode("utf-8")
    key_path = Path(os.path.expanduser("~/Desktop/SSOT_Agentic_Brain/.sovereign/crypto_keys/hmac_hardware_key.bin"))
    if key_path.is_file():
        return key_path.read_bytes()
    return b"XORAS_SOVEREIGN_HARDWARE_KEY_2026_M4"

SECRET_KEY = get_hmac_key()

class ContextLineageEngine:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS lineage_nodes (
                    node_id TEXT PRIMARY KEY,
                    seq_num INTEGER NOT NULL,
                    parent_hash TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    agent_id TEXT NOT NULL,
                    step_type TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    payload_raw TEXT NOT NULL,
                    payload_summary TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    merkle_root TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON lineage_nodes(session_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_parent ON lineage_nodes(parent_hash);")
            # Auto-migrate older schema if seq_num or payload_raw is missing
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(lineage_nodes);")
            cols = [row[1] for row in cur.fetchall()]
            if cols and "seq_num" not in cols:
                conn.execute("ALTER TABLE lineage_nodes ADD COLUMN seq_num INTEGER NOT NULL DEFAULT 0;")
            if cols and "payload_raw" not in cols:
                conn.execute("ALTER TABLE lineage_nodes ADD COLUMN payload_raw TEXT NOT NULL DEFAULT '';")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_seq ON lineage_nodes(session_id, seq_num);")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS global_evidence_registry (
                    evidence_digest TEXT PRIMARY KEY,
                    first_session_id TEXT NOT NULL,
                    first_node_id TEXT NOT NULL,
                    first_timestamp REAL NOT NULL,
                    agent_id TEXT NOT NULL,
                    step_type TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_evidence_digest ON global_evidence_registry(evidence_digest);")
            conn.commit()

    @staticmethod
    def compute_hash(data: str) -> str:
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    @staticmethod
    def compute_hmac(node_id: str, payload_hash: str) -> str:
        msg = f"{node_id}:{payload_hash}".encode('utf-8')
        return hmac.new(SECRET_KEY, msg, hashlib.sha256).hexdigest()

    def get_latest_node(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM lineage_nodes 
                WHERE session_id = ? 
                ORDER BY seq_num DESC, timestamp DESC LIMIT 1
            """, (session_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def calculate_merkle_root(self, session_id: str) -> str:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT node_id FROM lineage_nodes 
                WHERE session_id = ? 
                ORDER BY seq_num ASC, node_id ASC
            """, (session_id,))
            hashes = [row[0] for row in cur.fetchall()]
        
        if not hashes:
            return self.compute_hash("GENESIS_EMPTY_TREE")
        
        while len(hashes) > 1:
            next_hashes = []
            for i in range(0, len(hashes), 2):
                if i + 1 < len(hashes):
                    combined = hashes[i] + hashes[i+1]
                    next_hashes.append(self.compute_hash(combined))
                else:
                    next_hashes.append(hashes[i])
            hashes = next_hashes
        
        return hashes[0]

    def calculate_global_merkle_root(self) -> str:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT node_id FROM lineage_nodes ORDER BY timestamp ASC, rowid ASC")
            hashes = [row[0] for row in cur.fetchall()]
        
        if not hashes:
            return self.compute_hash("GENESIS_EMPTY_TREE")
        
        while len(hashes) > 1:
            next_hashes = []
            for i in range(0, len(hashes), 2):
                if i + 1 < len(hashes):
                    combined = hashes[i] + hashes[i+1]
                    next_hashes.append(self.compute_hash(combined))
                else:
                    next_hashes.append(hashes[i])
            hashes = next_hashes
        
        return hashes[0]

    def sync_global_merkle_root(self) -> str:
        global_root = self.calculate_global_merkle_root()
        merkle_file = os.path.expanduser("~/Desktop/SSOT_Agentic_Brain/memory/tri_brain/merkle_root.hash")
        os.makedirs(os.path.dirname(merkle_file), exist_ok=True)
        with open(merkle_file, "w", encoding="utf-8") as f:
            f.write(f"{global_root}\n")
        return global_root

    def commit_step(self, 
                    session_id: str, 
                    agent_id: str, 
                    step_type: str, 
                    payload: Dict[str, Any],
                    parent_hash: Optional[str] = None,
                    timestamp: Optional[float] = None) -> Dict[str, Any]:
        """
        Commits a new execution step with anti-corruption and anti-replay validation.
        """
        ts = time.time() if timestamp is None else timestamp
        payload_str = json.dumps(payload, sort_keys=True)
        payload_hash = self.compute_hash(payload_str)
        payload_summary = payload_str[:120]

        latest = self.get_latest_node(session_id)
        if latest is not None:
            # 1. Anti-Replay: Monotonic Timestamp & Sequence Enforcement
            if ts < latest["timestamp"]:
                raise ValueError(f"REPLAY_ATTACK_REJECTED: Non-monotonic backdated timestamp {ts} < {latest['timestamp']}")
            seq_num = latest["seq_num"] + 1
            if parent_hash is None:
                parent_hash = latest["node_id"]
        else:
            seq_num = 1
            if parent_hash is None:
                parent_hash = "GENESIS_NODE_0000000000000000"

        # Node ID is deterministic digest of (parent_hash, session_id, seq_num, ts, agent_id, step_type, payload_hash)
        node_raw = f"{parent_hash}:{session_id}:{seq_num}:{ts:.6f}:{agent_id}:{step_type}:{payload_hash}"
        node_id = self.compute_hash(node_raw)
        
        # 2. Anti-Replay: Global Duplicate Node Rejection
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT node_id FROM lineage_nodes WHERE node_id = ?", (node_id,))
            if cur.fetchone() is not None:
                raise ValueError(f"REPLAY_ATTACK_REJECTED: Duplicate node ID {node_id} already exists in registry.")

        # Compute HMAC signature for hardware-authenticated authenticity
        signature = self.compute_hmac(node_id, payload_hash)
        merkle_root = self.compute_hash(f"{parent_hash}:{node_id}")

        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO lineage_nodes 
                (node_id, seq_num, parent_hash, session_id, timestamp, agent_id, step_type, payload_hash, payload_raw, payload_summary, signature, merkle_root)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (node_id, seq_num, parent_hash, session_id, ts, agent_id, step_type, payload_hash, payload_str, payload_summary, signature, merkle_root))
            conn.commit()

        # Update actual session Merkle root across all nodes
        full_merkle_root = self.calculate_merkle_root(session_id)
        with self._get_conn() as conn:
            conn.execute("UPDATE lineage_nodes SET merkle_root = ? WHERE node_id = ?", (full_merkle_root, node_id))
            conn.commit()

        # Update global Merkle root file for Witness verification
        self.sync_global_merkle_root()

        # Register in global evidence registry (first session to introduce this finding owns provenance)
        if step_type != "ADVERSARIAL_ATTACK_INTERCEPTED":
            with self._get_conn() as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO global_evidence_registry 
                    (evidence_digest, first_session_id, first_node_id, first_timestamp, agent_id, step_type)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (payload_hash, session_id, node_id, ts, agent_id, step_type))

                if isinstance(payload, dict) and "signal" in payload and isinstance(payload["signal"], dict):
                    sig = payload["signal"]
                    finding_text = f"{sig.get('title', '')}:{sig.get('summary', '')}"
                    f_digest = hashlib.sha256(finding_text.encode('utf-8')).hexdigest()
                    conn.execute("""
                        INSERT OR IGNORE INTO global_evidence_registry 
                        (evidence_digest, first_session_id, first_node_id, first_timestamp, agent_id, step_type)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (f_digest, session_id, node_id, ts, agent_id, step_type))
                conn.commit()

        return {
            "node_id": node_id,
            "seq_num": seq_num,
            "parent_hash": parent_hash,
            "session_id": session_id,
            "timestamp": ts,
            "agent_id": agent_id,
            "step_type": step_type,
            "payload_hash": payload_hash,
            "signature": signature,
            "merkle_root": full_merkle_root
        }

    def check_cross_session_replay(self, session_id: str, payload_hash: str, cross_session_pointer: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Detects subtle cross-session replay where authentic payload data from an earlier session
        is submitted in a new session without valid lineage pointers (CLIA attack vector).
        """
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM global_evidence_registry WHERE evidence_digest = ?", (payload_hash,))
            row = cur.fetchone()
            if not row:
                return {"is_replay": False, "status": "FIRST_TIME_DISCOVERY"}
            
            origin = dict(row)
            if origin["first_session_id"] == session_id:
                return {"is_replay": False, "status": "SAME_SESSION_INTAKE"}

            # Cross-session detected!
            if not cross_session_pointer:
                return {
                    "is_replay": True,
                    "error": "CROSS_SESSION_UNLINKED_REPLAY",
                    "reason": f"Payload digest {payload_hash[:16]} originated in session '{origin['first_session_id']}' at node '{origin['first_node_id']}', but was submitted without cross-session lineage proof.",
                    "origin_session_id": origin["first_session_id"],
                    "origin_node_id": origin["first_node_id"],
                    "origin_timestamp": origin["first_timestamp"]
                }
            
            # Verify pointer authenticity
            src_session = cross_session_pointer.get("source_session_id")
            src_node = cross_session_pointer.get("source_node_id")
            if src_session != origin["first_session_id"] or src_node != origin["first_node_id"]:
                return {
                    "is_replay": True,
                    "error": "CROSS_SESSION_FORGED_POINTER",
                    "reason": f"Cross-session pointer mismatch: points to {src_session}/{src_node}, true origin is {origin['first_session_id']}/{origin['first_node_id']}"
                }
            
            # Verify that the origin node actually exists in active DAG
            cur.execute("SELECT node_id FROM lineage_nodes WHERE node_id = ?", (src_node,))
            node_row = cur.fetchone()
            if not node_row:
                return {
                    "is_replay": True,
                    "error": "CROSS_SESSION_SEVERED_ORIGIN",
                    "reason": f"Referenced source node {src_node} not found in active DAG."
                }

            return {
                "is_replay": False,
                "status": "ACCEPTED_WITH_EVIDENCE_POINTERS",
                "origin_session_id": origin["first_session_id"],
                "origin_node_id": origin["first_node_id"]
            }

    def commit_adversarial_interception(self, session_id: str, agent_id: str, attack_class: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Commits an immutable interception receipt into the Merkle DAG when an adversarial attack
        (corruption, backdating, duplicate replay, or orphan injection) is thwarted at the context bridge.
        """
        payload = {
            "attack_class": attack_class,
            "expected_invariants": details.get("expected_invariants", []),
            "observed_dispositions": details.get("observed_dispositions", ["INTERCEPTED_AND_QUARANTINED", "FAIL_CLOSED"]),
            "evidence_digest": details.get("evidence_digest", ""),
            "state_pollution": "ZERO_STATE_POLLUTION",
            "metadata": details.get("metadata", {})
        }
        return self.commit_step(
            session_id=session_id,
            agent_id=agent_id,
            step_type="ADVERSARIAL_ATTACK_INTERCEPTED",
            payload=payload
        )

    def verify_lineage(self, session_id: str) -> Dict[str, Any]:
        """
        Traverses the full session lineage DAG and verifies:
        - Structural DAG parent linkages.
        - HMAC signature integrity.
        - Payload anti-corruption (recomputing payload hash from raw storage).
        - Monotonic sequence numbers and non-replayed timestamps.
        - Session Merkle root consistency.
        """
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM lineage_nodes 
                WHERE session_id = ? 
                ORDER BY seq_num ASC, timestamp ASC
            """, (session_id,))
            rows = [dict(r) for r in cur.fetchall()]

        if not rows:
            return {"valid": True, "node_count": 0, "status": "EMPTY_SESSION"}

        known_nodes = {node["node_id"] for node in rows}
        known_nodes.add("GENESIS_NODE_0000000000000000")
        violations = []
        last_seq = 0
        last_seq = 0
        last_ts = 0.0
        prev_node_id = None

        for idx, node in enumerate(rows):
            # 1. Structural Parent Linkage & Initial Sequence Check
            parent = node["parent_hash"]
            if idx == 0:
                if node["seq_num"] != 1:
                    violations.append({
                        "node_id": node["node_id"],
                        "error": "INITIAL_SEQUENCE_GAP_DETECTED",
                        "seq_num": node["seq_num"]
                    })
                if not parent.startswith("GENESIS"):
                    violations.append({
                        "node_id": node["node_id"],
                        "error": "ROOT_GENESIS_PARENT_MISMATCH",
                        "actual_parent": parent
                    })
            else:
                if parent != prev_node_id:
                    violations.append({
                        "node_id": node["node_id"],
                        "error": "BROKEN_PARENT_CHAIN_LINEAR_DESYNC",
                        "expected_parent": prev_node_id,
                        "actual_parent": parent
                    })

            prev_node_id = node["node_id"]

            # 2. Node ID Metadata Re-computation Check
            expected_node_id = self.compute_hash(f"{node['parent_hash']}:{session_id}:{node['seq_num']}:{node['timestamp']:.6f}:{node['agent_id']}:{node['step_type']}:{node['payload_hash']}")
            if node["node_id"] != expected_node_id:
                violations.append({
                    "node_id": node["node_id"],
                    "error": "NODE_METADATA_TAMPERING_DETECTED",
                    "expected_node_id": expected_node_id,
                    "recorded_node_id": node["node_id"]
                })

            # 3. Evidence Corruption Check: Verify Payload Raw Hash Matches Recorded Digest
            computed_payload_hash = self.compute_hash(node["payload_raw"])
            if computed_payload_hash != node["payload_hash"]:
                violations.append({
                    "node_id": node["node_id"],
                    "error": "EVIDENCE_CORRUPTION_PAYLOAD_TAMPERED",
                    "expected": computed_payload_hash,
                    "recorded": node["payload_hash"]
                })

            # 4. HMAC Signature Integrity
            expected_sig = self.compute_hmac(node["node_id"], node["payload_hash"])
            if node["signature"] != expected_sig:
                violations.append({
                    "node_id": node["node_id"],
                    "error": "SIGNATURE_MUTATION_DETECTED",
                    "expected": expected_sig,
                    "actual": node["signature"]
                })

            # 5. Anti-Replay: Sequence & Monotonic Timestamp Check
            if node["seq_num"] <= last_seq:
                violations.append({
                    "node_id": node["node_id"],
                    "error": "REPLAY_ATTACK_SEQUENCE_COLLAPSE",
                    "seq_num": node["seq_num"],
                    "last_seq": last_seq
                })
            if node["timestamp"] < last_ts:
                violations.append({
                    "node_id": node["node_id"],
                    "error": "REPLAY_ATTACK_BACKDATED_TIMESTAMP",
                    "timestamp": node["timestamp"],
                    "last_timestamp": last_ts
                })

            last_seq = node["seq_num"]
            last_ts = node["timestamp"]

        # 5. Merkle Root Consistency Check
        computed_root = self.calculate_merkle_root(session_id)
        latest_node_root = rows[-1]["merkle_root"] if rows else ""
        if computed_root != latest_node_root:
            violations.append({
                "error": "MERKLE_ROOT_DESYNC",
                "computed": computed_root,
                "recorded": latest_node_root
            })

        return {
            "valid": len(violations) == 0,
            "session_id": session_id,
            "node_count": len(rows),
            "merkle_root": computed_root,
            "violations": violations
        }

if __name__ == "__main__":
    engine = ContextLineageEngine()
    session = "anti_corruption_test_session"
    res1 = engine.commit_step(session, "maxx", "PROMPT_INTAKE", {"prompt": "Build anti-corruption gate"})
    res2 = engine.commit_step(session, "jarvis", "TOOL_EXECUTION", {"command": "python3 audit.py", "exit_code": 0})
    audit = engine.verify_lineage(session)
    print(json.dumps(audit, indent=2))
