"""
XORAS Dart Runtime — process-wide Dart DB singleton + Stage 1 Wake helpers
==========================================================================
All agents, CLI, voice, and orchestrators MUST use this module instead of
constructing bare DartMemoryManager instances for production paths.

Hot ring remains available for unit tests via dart_ring_buffer.py.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.memory.dart_db import DEFAULT_ROOT, DartDb

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # repo root, computed from this file
WAKE_RECEIPT = PROJECT_ROOT / "memory" / "catch_log" / "DART_STAGE1_WAKE_RECEIPT.json"
PROCESS_JOURNAL = PROJECT_ROOT / "memory" / "journals" / "dart_db_process.jsonl"

_lock = threading.Lock()
_instance: Optional[DartDb] = None


def get_dart_db(force_reload: bool = False) -> DartDb:
    """Return the process-wide DartDb (creates on first call)."""
    global _instance
    with _lock:
        if _instance is None or force_reload:
            _instance = DartDb(
                root=DEFAULT_ROOT,
                capacity=4096,
                epoch_size=256,
                auto_safe_point_every=1024,
            )
            _journal(
                {
                    "event": "dart_db_open",
                    "write_ptr": _instance.total_writes,
                    "merkle_root": _instance.merkle_root,
                    "root": str(_instance.root),
                }
            )
        return _instance


def record_transition(
    agent_id: int,
    action_hash: int,
    state_flags: int,
    payload_data: bytes,
) -> int:
    """Canonical write path for every agent transition."""
    db = get_dart_db()
    seq = db.record(agent_id, action_hash, state_flags, payload_data)
    _journal(
        {
            "event": "dart_record",
            "sequence": seq,
            "agent_id": agent_id,
            "state_flags": state_flags,
        }
    )
    return seq


def stage1_wake_hydrate(limit: int = 50) -> Dict[str, Any]:
    """
    Stage 1 Wake Contract — LIFO hydrate preceding transitions.
    Writes DART_STAGE1_WAKE_RECEIPT.json for process audit.
    """
    db = get_dart_db()
    backlog = db.recall_backlog(limit=limit)
    receipt = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "contract": "STAGE_1_WAKE",
        "limit": limit,
        "recalled": len(backlog),
        "write_ptr": db.total_writes,
        "merkle_root": db.merkle_root,
        "first_sequence": backlog[0]["sequence"] if backlog else None,
        "last_sequence": backlog[-1]["sequence"] if backlog else None,
        "verdict": "WAKE_HYDRATED" if backlog or db.total_writes == 0 else "WAKE_EMPTY",
    }
    WAKE_RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    WAKE_RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    _journal({"event": "stage1_wake", **receipt})
    return {"receipt": receipt, "backlog": backlog}


def checkpoint_and_promote(label: str, proof_receipt: str = "") -> Dict[str, Any]:
    """Freeze Dart DB and refresh sovereign safe points."""
    db = get_dart_db()
    meta = db.checkpoint(label=label, promote_sovereign=True, proof_receipt=proof_receipt)
    out = {
        "checkpoint_id": meta.checkpoint_id,
        "sovereign_snapshot_id": meta.sovereign_snapshot_id,
        "merkle_root": meta.merkle_root,
        "write_ptr": meta.write_ptr,
    }
    _journal({"event": "dart_checkpoint_promote", **out})
    return out


def status() -> Dict[str, Any]:
    return get_dart_db().status()


def durable_paths() -> List[str]:
    """Paths that must be included in any full-system rollback snapshot."""
    root = DEFAULT_ROOT
    return [
        str(root / "wal.jsonl"),
        str(root / "state.json"),
        str(root / "merkle_epochs.jsonl"),
        str(root / "cold.sqlite"),
        str(root / "checkpoint_index.jsonl"),
    ]


def _journal(payload: Dict[str, Any]) -> None:
    PROCESS_JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    row = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **payload}
    with open(PROCESS_JOURNAL, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
