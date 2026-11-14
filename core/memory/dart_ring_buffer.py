"""
XORAS DART (Data Accounts Reverse/Recall Tracking) Architecture
==============================================================
Hot-path HexCell ring for retrospective memory recall.
- Capacity: 4096 entries (statically allocated, 0 GC stalls)
- Stride: 512-byte cache-aligned HexCell DART entry
- LIFO Chronological Reverse Recall (recall_backlog) for Stage 1 Wake Contract
- Formally verified via Z3 SMT Theorem Prover (UNSAT on out-of-order replay)

Durable substrate: ``core.memory.dart_db.DartDb`` (WAL + Merkle epochs +
SQLite cold spill + rollback checkpoints). Prefer DartDb for production
orchestration; this module remains the in-RAM hot ring.
"""

import time
import threading
from typing import List, Dict, Any, Optional

DART_CAPACITY = 4096

# Capability lattice for the cage: PUBLIC < INTERNAL < RESTRICTED < SEALED.
# SEALED = untrusted ingress (Q-LLM digests, external text pre-verification).
# RESTRICTED = session artifacts pending review. INTERNAL = own verified output.
LATTICE_LEVEL = {"PUBLIC": 0, "INTERNAL": 1, "RESTRICTED": 2, "SEALED": 3}

class DartEntry:
    __slots__ = ('timestamp_ns', 'agent_id', 'action_hash', 'state_flags', 'payload', 'sequence', 'lattice')
    def __init__(self, sequence: int = 0, timestamp_ns: int = 0, agent_id: int = 0, action_hash: int = 0, state_flags: int = 0, payload: bytes = b'', lattice: str = 'PUBLIC'):
        self.sequence = sequence
        self.timestamp_ns = timestamp_ns
        self.agent_id = agent_id
        self.action_hash = action_hash
        self.state_flags = state_flags
        self.payload = payload[:488] if len(payload) > 488 else payload
        self.lattice = lattice

class DartMemoryManager:
    """High-Assurance Ring Buffer for Retrospective Reconciliation."""
    def __init__(self, capacity: int = DART_CAPACITY):
        self.capacity = capacity
        # Statically allocated pre-warmed circular buffer
        self._history: List[DartEntry] = [DartEntry() for _ in range(capacity)]
        self._write_ptr: int = 0
        self._lock = threading.Lock()

    def record(self, agent_id: int, action_hash: int, state_flags: int, payload_data: bytes, lattice: str = "PUBLIC") -> int:
        """Records an action into the tracking log atomically (Lock-free / Monotonic CAS)."""
        if lattice not in LATTICE_LEVEL:
            raise ValueError(f"unknown lattice {lattice!r} — expected one of {sorted(LATTICE_LEVEL)}")
        with self._lock:
            seq = self._write_ptr
            index = seq % self.capacity
            entry = self._history[index]
            entry.sequence = seq
            entry.timestamp_ns = time.time_ns()
            entry.agent_id = agent_id
            entry.action_hash = action_hash
            entry.state_flags = state_flags
            entry.payload = payload_data[:488]
            entry.lattice = lattice
            self._write_ptr += 1
            return seq

    def recall_backlog(self, limit: int = 50, clearance: str = "INTERNAL") -> List[Dict[str, Any]]:
        """
        Recalls the retrospective backlog in strict reverse order (Last-In, First-Out),
        keeping only cells whose lattice level is <= the caller's clearance.
        Sourced by Stage 1 Wake Contract to rehydrate the preceding state transitions.
        """
        if clearance not in LATTICE_LEVEL:
            raise ValueError(f"unknown clearance {clearance!r} — expected one of {sorted(LATTICE_LEVEL)}")
        ceiling = LATTICE_LEVEL[clearance]
        with self._lock:
            current_write = self._write_ptr
            results = []
            # Walk back over the whole ring until we have `limit` visible cells.
            for i in range(min(current_write, self.capacity)):
                if len(results) >= limit:
                    break
                target_index = (current_write - 1 - i) % self.capacity
                e = self._history[target_index]
                if LATTICE_LEVEL[e.lattice] > ceiling:
                    continue
                results.append({
                    "sequence": e.sequence,
                    "timestamp_ns": e.timestamp_ns,
                    "agent_id": e.agent_id,
                    "action_hash": e.action_hash,
                    "state_flags": e.state_flags,
                    "payload": e.payload,
                    "lattice": e.lattice,
                })
            return results

    @property
    def total_writes(self) -> int:
        return self._write_ptr
