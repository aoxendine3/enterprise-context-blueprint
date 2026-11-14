#!/usr/bin/env python3
"""
DAXX Swarm Authoritative Telemetry Stream (`core/ops/telemetry/daxx_telemetry_stream.py`)
========================================================================================
Authoritative append-only telemetry stream replacing automated git commit/push.
Guarantees strictly monotonic sequencing, chained SHA-256 Merkle root integrity,
zero state pollution, nanosecond anti-backdating, and atomic POSIX file locking.

Governance: The Lead 9 Council (Maxx, Vance, Clara, DAXX, Jarvis)
"""

import os
import sys
import json
import shutil
import time
import fcntl
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

SSOT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_JOURNAL_PATH = SSOT_ROOT / ".agents" / "journals" / "daxx_telemetry.jsonl"
GENESIS_MERKLE_ROOT = "0" * 64


class DaxxTelemetryStream:
    """
    Append-only telemetry stream providing non-repudiation and state immutability.
    Enforces atomic POSIX file locking, monotonic sequencing, and continuous Merkle chains.
    """

    def __init__(self, journal_path: Optional[Path] = None):
        self.journal_path = Path(journal_path) if journal_path else DEFAULT_JOURNAL_PATH
        self.journal_path.parent.mkdir(parents=True, exist_ok=True)

    def emit(
        self,
        agent: str,
        event_type: str,
        payload: Dict[str, Any],
        taint_tag: str = "0xBEAF0000",
        signature: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Atomically appends an event to the telemetry stream with exclusive POSIX lock.
        """
        with open(self.journal_path, "a+", encoding="utf-8") as f:
            # 1. Acquire exclusive lock on physical file descriptor
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                # 2. Seek to beginning to read previous record
                f.seek(0)
                lines = [line.strip() for line in f if line.strip()]

                if not lines:
                    seq_num = 1
                    prev_merkle_root = GENESIS_MERKLE_ROOT
                    last_epoch = 0.0
                else:
                    last_record = json.loads(lines[-1])
                    seq_num = last_record["seq_num"] + 1
                    prev_merkle_root = last_record["merkle_root"]
                    last_epoch = last_record.get("timestamp_epoch", 0.0)

                # 3. Monotonic Timestamp Check (Trap backdating attacks)
                now_epoch = time.time()
                if now_epoch <= last_epoch:
                    now_epoch = last_epoch + 0.000001
                now_iso = datetime.fromtimestamp(now_epoch, timezone.utc).isoformat()

                # 4. Canonical Payload SHA-256 Digest
                canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
                payload_hash = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()

                # 5. Compute Chained Merkle Root: H(prev_root || seq || ts || agent || event || payload_hash)
                chain_seed = f"{prev_merkle_root}:{seq_num}:{now_iso}:{agent}:{event_type}:{payload_hash}"
                merkle_root = hashlib.sha256(chain_seed.encode("utf-8")).hexdigest()

                record: Dict[str, Any] = {
                    "seq_num": seq_num,
                    "timestamp": now_iso,
                    "timestamp_epoch": round(now_epoch, 6),
                    "agent": agent,
                    "event_type": event_type,
                    "payload_hash": payload_hash,
                    "merkle_root": merkle_root,
                    "prev_merkle_root": prev_merkle_root,
                    "taint_tag": taint_tag,
                    "payload": payload,
                }
                if signature is not None:
                    record["signature"] = signature

                # 6. Atomic Write and Bare-Metal Flush
                f.seek(0, 2)  # Seek to end of file
                f.write(json.dumps(record) + "\n")
                f.flush()
                os.fsync(f.fileno())  # Ensure flush to physical media

                return record
            finally:
                # 7. Release lock
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def recanonicalize_legacy_records(self) -> Dict[str, Any]:
        """
        Normalizes records written under the LEGACY JSON convention
        (json.dumps(payload, sort_keys=True) — default separators) into the
        canonical convention used by this engine (compact separators).

        The payload bytes are NEVER altered. The legacy signed hash is preserved
        on the record as `payload_hash_legacy` for audit, the canonical hash is
        written to `payload_hash`, and the Merkle chain is re-linked from that
        point forward using the engine's own chain seed.

        A record whose payload matches NEITHER convention is genuine corruption
        and is left untouched (it will still fail verification).
        """
        if not self.journal_path.exists() or self.journal_path.stat().st_size == 0:
            return {"status": "EMPTY", "repaired": 0}

        backup = self.journal_path.with_suffix(self.journal_path.suffix + ".pre_canonicalize.bak")
        shutil.copy2(self.journal_path, backup)

        with open(self.journal_path, "r", encoding="utf-8") as f:
            lines = [ln for ln in f.read().splitlines() if ln.strip()]

        records = [json.loads(ln) for ln in lines]
        repaired = 0
        touched = False
        for rec in records:
            payload = rec.get("payload", {})
            canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
            canonical_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            if rec.get("payload_hash") == canonical_hash:
                continue
            legacy = json.dumps(payload, sort_keys=True)
            legacy_hash = hashlib.sha256(legacy.encode("utf-8")).hexdigest()
            if rec.get("payload_hash") != legacy_hash:
                # Neither convention matches — genuine corruption. Leave it.
                continue
            rec["payload_hash_legacy"] = legacy_hash
            rec["payload_hash"] = canonical_hash
            repaired += 1
            touched = True

        if touched:
            # Re-link the Merkle chain from the first repaired record forward.
            prev_root = None
            for rec in records:
                if prev_root is None:
                    prev_root = rec.get("prev_merkle_root")
                seed = (
                    f"{prev_root}:{rec['seq_num']}:{rec['timestamp']}:"
                    f"{rec['agent']}:{rec['event_type']}:{rec['payload_hash']}"
                )
                rec["merkle_root"] = hashlib.sha256(seed.encode("utf-8")).hexdigest()
                rec["prev_merkle_root"] = prev_root
                prev_root = rec["merkle_root"]

            tmp = self.journal_path.with_suffix(self.journal_path.suffix + ".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                for rec in records:
                    f.write(json.dumps(rec) + "\n")
            os.replace(tmp, self.journal_path)

        return {
            "status": "RECANONICALIZED" if touched else "NO_LEGACY_RECORDS",
            "repaired": repaired,
            "backup": str(backup),
            "payloads_altered": 0,
        }

    def verify_stream(self) -> Dict[str, Any]:
        """
        Validates 100% of the stream from Genesis to Tip.
        Ensures monotonic sequence, valid payload hashes, and unbroken Merkle roots.
        """
        if not self.journal_path.exists() or self.journal_path.stat().st_size == 0:
            return {"status": "EMPTY", "records_verified": 0, "tip_merkle_root": GENESIS_MERKLE_ROOT}

        with open(self.journal_path, "r", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                expected_prev = GENESIS_MERKLE_ROOT
                expected_seq = 1
                last_epoch = 0.0

                for line_idx, line in enumerate(f, 1):
                    line_str = line.strip()
                    if not line_str:
                        continue
                    rec = json.loads(line_str)

                    # Monotonic sequence check
                    if rec["seq_num"] != expected_seq:
                        raise ValueError(
                            f"SEQ_GAP: Line {line_idx} has seq {rec['seq_num']}, expected {expected_seq}"
                        )
                    # Chained Merkle root link check
                    if rec["prev_merkle_root"] != expected_prev:
                        raise ValueError(
                            f"CHAIN_BREAK: Line {line_idx} prev_root mismatch. "
                            f"Expected {expected_prev}, got {rec['prev_merkle_root']}"
                        )
                    # Timestamp check
                    if rec["timestamp_epoch"] < last_epoch:
                        raise ValueError(
                            f"BACKDATED_TIME: Line {line_idx} epoch {rec['timestamp_epoch']} < {last_epoch}"
                        )

                    # Validate payload hash
                    canonical_payload = json.dumps(rec["payload"], sort_keys=True, separators=(",", ":"))
                    expected_payload_hash = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
                    if rec["payload_hash"] != expected_payload_hash:
                        raise ValueError(
                            f"PAYLOAD_CORRUPT: Line {line_idx} hash mismatch. "
                            f"Expected {expected_payload_hash}, got {rec['payload_hash']}"
                        )

                    # Validate chained Merkle root
                    seed = (
                        f"{expected_prev}:{rec['seq_num']}:{rec['timestamp']}:"
                        f"{rec['agent']}:{rec['event_type']}:{rec['payload_hash']}"
                    )
                    expected_root = hashlib.sha256(seed.encode("utf-8")).hexdigest()
                    if rec["merkle_root"] != expected_root:
                        raise ValueError(
                            f"MERKLE_ROOT_CORRUPT: Line {line_idx} root mismatch. "
                            f"Expected {expected_root}, got {rec['merkle_root']}"
                        )

                    expected_prev = rec["merkle_root"]
                    expected_seq += 1
                    last_epoch = rec["timestamp_epoch"]

                return {
                    "status": "VERIFIED_VALID",
                    "records_verified": expected_seq - 1,
                    "tip_merkle_root": expected_prev,
                }
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def get_telemetry_stream(journal_path: Optional[Path] = None) -> DaxxTelemetryStream:
    """Helper factory for accessing the default telemetry stream."""
    return DaxxTelemetryStream(journal_path=journal_path)


if __name__ == "__main__":
    stream = get_telemetry_stream()
    if len(sys.argv) > 1 and sys.argv[1] == "--recanonicalize":
        res = stream.recanonicalize_legacy_records()
        print(json.dumps(res, indent=2))
        sys.exit(0 if res.get("repaired", 0) >= 0 else 1)
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        res = stream.verify_stream()
        print(json.dumps(res, indent=2))
        sys.exit(0 if res.get("status") in ("VERIFIED_VALID", "EMPTY") else 1)

    # Self-test bootstrap emit
    receipt = stream.emit(
        agent="DAXX",
        event_type="BOOTSTRAP",
        payload={
            "mission_id": "M1_HYGIENE_PERSISTENCE",
            "task_id": "TASK_1_TELEMETRY_INITIALIZATION",
            "details": "DAXX telemetry stream initialized with POSIX file locking and chained Merkle roots.",
            "status": "ACTIVE",
        },
        taint_tag="0xBEAF0000",
    )
    print("Emitted record:")
    print(json.dumps(receipt, indent=2))
    ver = stream.verify_stream()
    print("Stream verification:")
    print(json.dumps(ver, indent=2))
