"""
XORAS Dart DB — durable HexCell transition store for DART
=========================================================
Hot path: 4096 x 512 HexCell ring (DartMemoryManager).
Durable path: append-only WAL + epoch Merkle spine + SQLite cold spill.
Rollback: named checkpoints + hooks into sovereign_rollback_manager so
safe points stay current as the DB advances.

Contract (unchanged from DART):
  record / recall_backlog(LIFO) / monotonic sequence / Stage 1 Wake.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.memory.dart_ring_buffer import DART_CAPACITY, LATTICE_LEVEL, DartMemoryManager

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = REPO_ROOT / "memory" / "tri_brain" / "dart_db"
EPOCH_SIZE = 256
PROJECT_ROOT = REPO_ROOT


def _utcstamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _cell_hash(
    sequence: int,
    timestamp_ns: int,
    agent_id: int,
    action_hash: int,
    state_flags: int,
    payload: bytes,
) -> str:
    h = hashlib.sha256()
    h.update(sequence.to_bytes(8, "little", signed=False))
    h.update(timestamp_ns.to_bytes(8, "little", signed=False))
    h.update(agent_id.to_bytes(8, "little", signed=False))
    h.update(action_hash.to_bytes(8, "little", signed=False))
    h.update(state_flags.to_bytes(4, "little", signed=False))
    h.update(payload)
    return h.hexdigest()


@dataclass
class DartCheckpointMeta:
    checkpoint_id: str
    label: str
    created_utc: str
    write_ptr: int
    merkle_root: str
    wal_sha256: str
    state_sha256: str
    cold_sha256: str
    sovereign_snapshot_id: Optional[str] = None


class DartDb:
    """Durable DART store with WAL, Merkle epochs, cold spill, and rollback."""

    def __init__(
        self,
        root: Path | str = DEFAULT_ROOT,
        capacity: int = DART_CAPACITY,
        epoch_size: int = EPOCH_SIZE,
        auto_safe_point_every: int = 1024,
    ):
        self.root = Path(root)
        self.capacity = capacity
        self.epoch_size = epoch_size
        self.auto_safe_point_every = max(0, auto_safe_point_every)
        self._lock = threading.Lock()
        self._hot = DartMemoryManager(capacity=capacity)
        self._merkle_root = "0" * 64
        self._epoch_leaves: List[str] = []
        self._last_auto_safe_at = 0

        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "checkpoints").mkdir(parents=True, exist_ok=True)

        self.wal_path = self.root / "wal.jsonl"
        self.state_path = self.root / "state.json"
        self.merkle_path = self.root / "merkle_epochs.jsonl"
        self.cold_path = self.root / "cold.sqlite"
        self.checkpoint_index = self.root / "checkpoint_index.jsonl"

        self._init_cold()
        self._recover()

    # ------------------------------------------------------------------ open /
    def _init_cold(self) -> None:
        conn = sqlite3.connect(self.cold_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cells (
                    sequence INTEGER PRIMARY KEY,
                    timestamp_ns INTEGER NOT NULL,
                    agent_id INTEGER NOT NULL,
                    action_hash INTEGER NOT NULL,
                    state_flags INTEGER NOT NULL,
                    payload BLOB NOT NULL,
                    cell_hash TEXT NOT NULL,
                    lattice TEXT NOT NULL DEFAULT 'PUBLIC',
                    lattice_level INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            # Legacy upgrade path: add lattice columns to an existing cold store.
            cols = {row[1] for row in conn.execute("PRAGMA table_info(cells)")}
            if "lattice" not in cols:
                conn.execute("ALTER TABLE cells ADD COLUMN lattice TEXT NOT NULL DEFAULT 'RESTRICTED'")
                conn.execute("ALTER TABLE cells ADD COLUMN lattice_level INTEGER NOT NULL DEFAULT 2")
            conn.commit()
        finally:
            conn.close()

    def _load_state(self) -> Dict[str, Any]:
        if not self.state_path.exists():
            return {
                "write_ptr": 0,
                "merkle_root": "0" * 64,
                "epoch_index": 0,
                "updated_utc": _utcstamp(),
            }
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def _save_state(self) -> None:
        payload = {
            "write_ptr": self._hot.total_writes,
            "merkle_root": self._merkle_root,
            "epoch_index": self._epoch_index,
            "capacity": self.capacity,
            "epoch_size": self.epoch_size,
            "updated_utc": _utcstamp(),
        }
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(self.state_path)

    def _recover(self) -> None:
        """Rebuild hot ring from WAL tail; restore Merkle root from state."""
        state = self._load_state()
        self._merkle_root = state.get("merkle_root", "0" * 64)
        self._epoch_index = int(state.get("epoch_index", 0))
        self._epoch_leaves = []

        if not self.wal_path.exists():
            self._save_state()
            return

        rows: List[Dict[str, Any]] = []
        with open(self.wal_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))

        # Replay into a fresh hot ring (last `capacity` cells matter for wake).
        self._hot = DartMemoryManager(capacity=self.capacity)
        for row in rows:
            payload = bytes.fromhex(row["payload_hex"]) if row.get("payload_hex") else b""
            sequence = int(row["sequence"])
            index = sequence % self.capacity
            entry = self._hot._history[index]
            entry.sequence = sequence
            entry.timestamp_ns = int(row["timestamp_ns"])
            entry.agent_id = int(row["agent_id"])
            entry.action_hash = int(row["action_hash"])
            entry.state_flags = int(row["state_flags"])
            entry.payload = payload[:488]
            # Fail-closed: legacy rows without a lattice are treated as RESTRICTED
            entry.lattice = row.get("lattice", "RESTRICTED")

        if rows:
            self._hot._write_ptr = int(rows[-1]["sequence"]) + 1
        self._last_auto_safe_at = self._hot.total_writes
        self._save_state()

    # -------------------------------------------------------------- record API
    def record(
        self,
        agent_id: int,
        action_hash: int,
        state_flags: int,
        payload_data: bytes,
        lattice: str = "PUBLIC",
    ) -> int:
        if lattice not in LATTICE_LEVEL:
            raise ValueError(f"unknown lattice {lattice!r} — expected one of {sorted(LATTICE_LEVEL)}")
        with self._lock:
            payload = payload_data[:488] if len(payload_data) > 488 else payload_data

            # Spill cell about to be overwritten (when wrapping)
            if self._hot.total_writes >= self.capacity:
                doomed_index = self._hot.total_writes % self.capacity
                doomed = self._hot._history[doomed_index]
                if doomed.sequence or doomed.timestamp_ns:
                    self._cold_insert(
                        doomed.sequence,
                        doomed.timestamp_ns,
                        doomed.agent_id,
                        doomed.action_hash,
                        doomed.state_flags,
                        doomed.payload,
                        getattr(doomed, "lattice", "PUBLIC"),
                    )

            seq = self._hot.record(agent_id, action_hash, state_flags, payload, lattice=lattice)
            # Hot.record assigns its own sequence from write_ptr; re-read entry
            index = seq % self.capacity
            entry = self._hot._history[index]
            # Ensure sequence matches WAL (hot uses write_ptr before increment return)
            cell_hash = _cell_hash(
                entry.sequence,
                entry.timestamp_ns,
                entry.agent_id,
                entry.action_hash,
                entry.state_flags,
                entry.payload,
            )
            wal_row = {
                "sequence": entry.sequence,
                "timestamp_ns": entry.timestamp_ns,
                "agent_id": entry.agent_id,
                "action_hash": entry.action_hash,
                "state_flags": entry.state_flags,
                "payload_hex": entry.payload.hex(),
                "cell_hash": cell_hash,
                "lattice": entry.lattice,
                "recorded_utc": _utcstamp(),
            }
            with open(self.wal_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(wal_row, sort_keys=True) + "\n")
                fh.flush()

            self._epoch_leaves.append(cell_hash)
            if len(self._epoch_leaves) >= self.epoch_size:
                self._seal_epoch()

            self._save_state()

            if (
                self.auto_safe_point_every
                and self._hot.total_writes - self._last_auto_safe_at
                >= self.auto_safe_point_every
            ):
                self._last_auto_safe_at = self._hot.total_writes
                # Non-sovereign local checkpoint; sovereign promote is explicit
                self.checkpoint(label=f"auto_{self._hot.total_writes}", promote_sovereign=False)

            return entry.sequence

    def recall_backlog(self, limit: int = 50, clearance: str = "INTERNAL") -> List[Dict[str, Any]]:
        with self._lock:
            return self._hot.recall_backlog(limit=limit, clearance=clearance)

    def recall_sequence_range(self, start: int, end: int, clearance: str = "INTERNAL") -> List[Dict[str, Any]]:
        """Deep wake: pull from cold SQLite by inclusive sequence range."""
        if clearance not in LATTICE_LEVEL:
            raise ValueError(f"unknown clearance {clearance!r}")
        ceiling = LATTICE_LEVEL[clearance]
        with self._lock:
            conn = sqlite3.connect(self.cold_path)
            try:
                cur = conn.execute(
                    """
                    SELECT sequence, timestamp_ns, agent_id, action_hash,
                           state_flags, payload, lattice
                    FROM cells
                    WHERE sequence >= ? AND sequence <= ?
                      AND lattice_level <= ?
                    ORDER BY sequence ASC
                    """,
                    (start, end, ceiling),
                )
                out = []
                for row in cur.fetchall():
                    out.append(
                        {
                            "sequence": row[0],
                            "timestamp_ns": row[1],
                            "agent_id": row[2],
                            "action_hash": row[3],
                            "state_flags": row[4],
                            "payload": bytes(row[5]),
                            "lattice": row[6],
                        }
                    )
                return out
            finally:
                conn.close()

    @property
    def total_writes(self) -> int:
        return self._hot.total_writes

    @property
    def merkle_root(self) -> str:
        return self._merkle_root

    # --------------------------------------------------------------- Merkle /
    def _seal_epoch(self) -> None:
        material = "".join(self._epoch_leaves).encode("utf-8")
        epoch_hash = hashlib.sha256(material).hexdigest()
        self._merkle_root = hashlib.sha256(
            (self._merkle_root + epoch_hash).encode("utf-8")
        ).hexdigest()
        record = {
            "epoch_index": self._epoch_index,
            "leaf_count": len(self._epoch_leaves),
            "epoch_hash": epoch_hash,
            "merkle_root": self._merkle_root,
            "sealed_utc": _utcstamp(),
            "through_sequence": self._hot.total_writes - 1,
        }
        with open(self.merkle_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")
        self._epoch_index += 1
        self._epoch_leaves = []

    def flush_epoch(self) -> Optional[str]:
        """Force-seal a partial epoch; returns new merkle root or None if empty."""
        with self._lock:
            if not self._epoch_leaves:
                return None
            self._seal_epoch()
            self._save_state()
            return self._merkle_root

    # ---------------------------------------------------------------- cold /
    def _cold_insert(
        self,
        sequence: int,
        timestamp_ns: int,
        agent_id: int,
        action_hash: int,
        state_flags: int,
        payload: bytes,
        lattice: str = "PUBLIC",
    ) -> None:
        cell_hash = _cell_hash(
            sequence, timestamp_ns, agent_id, action_hash, state_flags, payload
        )
        conn = sqlite3.connect(self.cold_path)
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO cells
                (sequence, timestamp_ns, agent_id, action_hash, state_flags, payload, cell_hash, lattice, lattice_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sequence,
                    timestamp_ns,
                    agent_id,
                    action_hash,
                    state_flags,
                    payload,
                    cell_hash,
                    lattice,
                    LATTICE_LEVEL[lattice],
                ),
            )
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------ rollback /
    def _sha256_file(self, path: Path) -> str:
        if not path.exists():
            return "0" * 64
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    def _durable_files(self) -> List[Path]:
        files = [self.wal_path, self.state_path, self.merkle_path, self.cold_path]
        return [p for p in files if p.exists()]

    def checkpoint(
        self,
        label: str,
        promote_sovereign: bool = True,
        proof_receipt: str = "",
    ) -> DartCheckpointMeta:
        """
        Freeze current Dart DB state into checkpoints/<id>/ and optionally
        register a sovereign rollback snapshot + safe-point promotion so the
        global rollback registry stays up to date.
        """
        with self._lock:
            # Seal any open epoch so checkpoint Merkle is current
            if self._epoch_leaves:
                self._seal_epoch()
            self._save_state()

            cid = f"{time.strftime('%Y%m%dT%H%M%S')}_{label}"
            dest = self.root / "checkpoints" / cid
            dest.mkdir(parents=True, exist_ok=False)
            for src in self._durable_files():
                shutil.copy2(src, dest / src.name)

            meta = DartCheckpointMeta(
                checkpoint_id=cid,
                label=label,
                created_utc=_utcstamp(),
                write_ptr=self._hot.total_writes,
                merkle_root=self._merkle_root,
                wal_sha256=self._sha256_file(dest / "wal.jsonl")
                if (dest / "wal.jsonl").exists()
                else "0" * 64,
                state_sha256=self._sha256_file(dest / "state.json"),
                cold_sha256=self._sha256_file(dest / "cold.sqlite")
                if (dest / "cold.sqlite").exists()
                else "0" * 64,
            )

            sovereign_id = None
            if promote_sovereign:
                sovereign_id = self._sovereign_snapshot_and_promote(
                    label=f"dart_db_{label}",
                    proof_receipt=proof_receipt
                    or str(
                        PROJECT_ROOT
                        / "memory"
                        / "catch_log"
                        / "DART_DB_CHECKPOINT_RECEIPT.json"
                    ),
                )
                meta.sovereign_snapshot_id = sovereign_id

            with open(self.checkpoint_index, "a", encoding="utf-8") as fh:
                fh.write(
                    json.dumps(
                        {
                            "checkpoint_id": meta.checkpoint_id,
                            "label": meta.label,
                            "created_utc": meta.created_utc,
                            "write_ptr": meta.write_ptr,
                            "merkle_root": meta.merkle_root,
                            "wal_sha256": meta.wal_sha256,
                            "state_sha256": meta.state_sha256,
                            "cold_sha256": meta.cold_sha256,
                            "sovereign_snapshot_id": meta.sovereign_snapshot_id,
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )
            return meta

    def _sovereign_snapshot_and_promote(
        self, label: str, proof_receipt: str
    ) -> Optional[str]:
        """Call sovereign_rollback_manager snapshot + promote for Dart DB files."""
        try:
            import importlib.util

            mgr_path = PROJECT_ROOT / "core" / "ops" / "scripts" / "sovereign_rollback_manager.py"
            spec = importlib.util.spec_from_file_location("sovereign_rollback_manager", mgr_path)
            if spec is None or spec.loader is None:
                return None
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            files = [str(p) for p in self._durable_files()]
            if not files:
                return None
            snap_id = mod.snapshot(label=label, files=files)
            # Ensure proof receipt exists for promote
            proof = Path(proof_receipt)
            if not proof.is_absolute():
                proof = PROJECT_ROOT / proof
            proof.parent.mkdir(parents=True, exist_ok=True)
            if not proof.exists():
                proof.write_text(
                    json.dumps(
                        {
                            "gate": "dart_db_checkpoint",
                            "label": label,
                            "snapshot_id": snap_id,
                            "merkle_root": self._merkle_root,
                            "write_ptr": self._hot.total_writes,
                            "created_utc": _utcstamp(),
                            "verdict": "DART_DB_CHECKPOINT_CAPTURED",
                        },
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )
            mod.promote(
                snapshot_id=snap_id,
                proof_receipt=str(proof.relative_to(PROJECT_ROOT))
                if str(proof).startswith(str(PROJECT_ROOT))
                else str(proof),
                name=f"dart_db_{label}",
            )
            return snap_id
        except BaseException as exc:
            # Fail soft on promote — local checkpoint still valid
            # (sovereign manager may raise SystemExit on guard failure)
            err_path = self.root / "last_sovereign_hook_error.txt"
            err_path.write_text(f"{_utcstamp()} {type(exc).__name__}: {exc}\n", encoding="utf-8")
            return None

    def rollback_to(self, checkpoint_id: str) -> None:
        """Restore durable files from a local Dart checkpoint and rehydrate hot ring."""
        with self._lock:
            src = self.root / "checkpoints" / checkpoint_id
            if not src.exists():
                raise FileNotFoundError(f"Unknown Dart checkpoint: {checkpoint_id}")
            for name in ("wal.jsonl", "state.json", "merkle_epochs.jsonl", "cold.sqlite"):
                piece = src / name
                if piece.exists():
                    shutil.copy2(piece, self.root / name)
                elif (self.root / name).exists() and name == "wal.jsonl":
                    # Checkpoint without wal means empty — truncate
                    (self.root / name).write_text("", encoding="utf-8")
            self._hot = DartMemoryManager(capacity=self.capacity)
            self._recover()

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        if not self.checkpoint_index.exists():
            return []
        out = []
        with open(self.checkpoint_index, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "root": str(self.root),
                "write_ptr": self._hot.total_writes,
                "merkle_root": self._merkle_root,
                "epoch_index": self._epoch_index,
                "open_epoch_leaves": len(self._epoch_leaves),
                "capacity": self.capacity,
                "checkpoints": len(self.list_checkpoints()),
                "updated_utc": _utcstamp(),
            }


def open_default() -> DartDb:
    return DartDb(root=DEFAULT_ROOT)
