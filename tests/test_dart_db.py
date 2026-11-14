"""
XORAS Dart DB acceptance suite
==============================
WAL durability, wrap→cold spill, Merkle epoch seal, checkpoint rollback,
and sovereign safe-point hook (best-effort).
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # repo root
sys.path.insert(0, str(ROOT))

from core.memory.dart_db import DartDb, EPOCH_SIZE  # noqa: E402

RECEIPT = ROOT / "memory" / "catch_log" / "DART_DB_ACCEPTANCE_RECEIPT.json"


def _run() -> dict:
    tmp = Path(tempfile.mkdtemp(prefix="dart_db_test_"))
    results = {"tmp": str(tmp), "checks": {}}

    try:
        db = DartDb(root=tmp, capacity=64, epoch_size=8, auto_safe_point_every=0)

        # 1) Record + LIFO
        for i in range(20):
            db.record(100 + (i % 3), 0xA000 + i, 1, f"payload_{i}".encode())
        backlog = db.recall_backlog(10)
        assert len(backlog) == 10
        assert backlog[0]["sequence"] > backlog[-1]["sequence"]
        results["checks"]["lifo_hot"] = True

        # 2) WAL persisted
        assert (tmp / "wal.jsonl").exists()
        lines = (tmp / "wal.jsonl").read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 20
        results["checks"]["wal_durable"] = True

        # 3) Crash recovery — new instance same root
        db2 = DartDb(root=tmp, capacity=64, epoch_size=8, auto_safe_point_every=0)
        assert db2.total_writes == 20
        b2 = db2.recall_backlog(5)
        assert b2[0]["sequence"] == 19
        results["checks"]["wal_recover"] = True

        # 4) Wrap → cold spill
        for i in range(20, 100):
            db2.record(1, i, 1, f"wrap_{i}".encode())
        cold = db2.recall_sequence_range(0, 10)
        assert len(cold) >= 1
        results["checks"]["cold_spill"] = True
        results["cold_rows_sample"] = len(cold)

        # 5) Merkle epoch seal
        root_before = db2.merkle_root
        db2.flush_epoch()
        # force more epochs
        for i in range(100, 100 + EPOCH_SIZE):
            db2.record(2, i, 1, b"epoch")
        assert db2.merkle_root != "0" * 64
        assert (tmp / "merkle_epochs.jsonl").exists()
        results["checks"]["merkle_epochs"] = True
        results["merkle_root"] = db2.merkle_root
        results["root_before_flush_note"] = root_before

        # 6) Checkpoint + rollback
        meta = db2.checkpoint(label="pre_mutation", promote_sovereign=False)
        ptr_at_ckpt = db2.total_writes
        for i in range(30):
            db2.record(9, i, 1, b"after_ckpt")
        assert db2.total_writes == ptr_at_ckpt + 30
        db2.rollback_to(meta.checkpoint_id)
        assert db2.total_writes == ptr_at_ckpt
        results["checks"]["checkpoint_rollback"] = True
        results["checkpoint_id"] = meta.checkpoint_id

        # 7) Sovereign hook — seeds the LIVE tri_brain DART store.
        #    Opt-in only: DART_LIVE_BOOTSTRAP=1. A test must never mutate the
        #    production store by default, and every suite invocation was
        #    appending synthetic records + sovereign snapshots.
        if os.environ.get("DART_LIVE_BOOTSTRAP") == "1":
            live = DartDb(
                root=ROOT / "memory" / "tri_brain" / "dart_db",
                capacity=4096,
                epoch_size=256,
                auto_safe_point_every=0,
            )
            for i in range(16):
                live.record(42, 0xDADBEEF0 + i, 0x03, f"live_boot_{i}".encode())
            live_meta = live.checkpoint(
                label="dart_db_bootstrap",
                promote_sovereign=True,
                proof_receipt=str(ROOT / "memory" / "catch_log" / "DART_DB_CHECKPOINT_RECEIPT.json"),
            )
            results["checks"]["live_bootstrap"] = True
            results["live_checkpoint"] = live_meta.checkpoint_id
            results["sovereign_snapshot_id"] = live_meta.sovereign_snapshot_id
            results["live_status"] = live.status()
        else:
            results["checks"]["live_bootstrap"] = None  # skipped (set DART_LIVE_BOOTSTRAP=1 to seed live store)
            results.setdefault("notes", []).append("live_bootstrap skipped by default — pass DART_LIVE_BOOTSTRAP=1 to seed the live store")

        results["verdict"] = "VERIFIED_DART_DB_ACCEPTANCE"
        results["timestamp_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return results
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> None:
    print("=" * 70)
    print("XORAS DART DB ACCEPTANCE")
    print("=" * 70)
    receipt = _run()
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    print(f"\n[RECEIPT] {RECEIPT}")
    failed = [k for k, v in receipt["checks"].items() if v is False]
    if failed:
        raise SystemExit(f"FAILED: {failed}")
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
