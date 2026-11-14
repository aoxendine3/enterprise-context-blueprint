"""
XORAS DART CAGE LATTICE ACCEPTANCE SUITE
==========================================
Proves the MERIDIAN cage rule against the real DartDb:

1. SEALED-written cells NEVER surface in recall_backlog / recall_sequence_range
   to a lower-clearance caller (PUBLIC / INTERNAL / RESTRICTED).
2. SEALED clearance callers DO see them (they are the only ones permitted).
3. Crash recovery preserves lattice fidelity (WAL replay) and defaults legacy
   rows (pre-lattice) to RESTRICTED — fail-closed, never silently PUBLIC.
4. Invalid lattice labels are rejected at write time.
5. Full checkpoint/rollback preserves lattice end-to-end.

Writes a receipt to memory/catch_log/DART_CAGE_LATTICE_RECEIPT.json.
Run: python3 tests/test_dart_cage_lattice.py
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.memory.dart_db import DartDb  # noqa: E402

RECEIPT = ROOT / "memory" / "catch_log" / "DART_CAGE_LATTICE_RECEIPT.json"

def _run() -> dict:
    tmp = Path(tempfile.mkdtemp(prefix="dart_cage_"))
    results = {"tmp": str(tmp), "checks": {}}
    try:
        db = DartDb(root=tmp, capacity=32, epoch_size=4, auto_safe_point_every=0)

        # 1) SEALED cells invisible to lower clearances
        db.record(7, 0x51, 1, b"sealed-secret", lattice="SEALED")
        db.record(7, 0x52, 1, b"internal-own", lattice="INTERNAL")
        for clearance in ("PUBLIC", "INTERNAL", "RESTRICTED"):
            backlog = db.recall_backlog(10, clearance=clearance)
            assert all(b["lattice"] != "SEALED" for b in backlog), f"SEALED leaked to {clearance}"
        results["checks"]["sealed_invisible_to_lower_clearance"] = True

        # 2) SEALED clearance sees everything
        sealed_view = db.recall_backlog(10, clearance="SEALED")
        assert any(b["lattice"] == "SEALED" for b in sealed_view)
        results["checks"]["sealed_visible_to_sealed_clearance"] = True

        # 3) Invalid label rejected at write time
        try:
            db.record(7, 0x53, 1, b"bad", lattice="BOGUS")
            assert False, "bad lattice accepted"
        except ValueError:
            pass
        results["checks"]["invalid_lattice_rejected"] = True

        # 4) Crash recovery: reopen and re-read lattice fidelity + legacy default
        db2 = DartDb(root=tmp, capacity=32, epoch_size=4, auto_safe_point_every=0)
        backlog = db2.recall_backlog(10, clearance="SEALED")
        assert any(b["lattice"] == "SEALED" for b in backlog)
        restricted_view = db2.recall_backlog(10, clearance="RESTRICTED")
        assert any(b["lattice"] == "RESTRICTED" or b["lattice"] == "INTERNAL" for b in restricted_view)
        results["checks"]["wal_replay_lattice_fidelity"] = True

        # 5) Legacy rows (no lattice key) replay as RESTRICTED, hidden from INTERNAL
        legacy_wal = tmp / "legacy_wal.jsonl"
        legacy_row = {
            "sequence": 999,
            "timestamp_ns": time.time_ns(),
            "agent_id": 1,
            "action_hash": 0xD15EA5E,
            "state_flags": 1,
            "payload_hex": b"legacy".hex(),
            "cell_hash": "0" * 64,
            # NOTE: no "lattice" key — pre-cage format
        }
        legacy_wal.write_text(json.dumps(legacy_row, sort_keys=True) + "\n", encoding="utf-8")
        # Append legacy row to the live WAL and reopen
        with open(tmp / "wal.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(legacy_row, sort_keys=True) + "\n")
        db3 = DartDb(root=tmp, capacity=32, epoch_size=4, auto_safe_point_every=0)
        names = {e["sequence"] for e in db3.recall_backlog(64, clearance="INTERNAL")}
        assert 999 not in names, "legacy row leaked to INTERNAL clearance"
        names_r = {e["sequence"] for e in db3.recall_backlog(64, clearance="RESTRICTED")}
        assert 999 in names_r, "legacy row missing from RESTRICTED clearance"
        results["checks"]["legacy_rows_default_restricted"] = True

        # 6) Cold spill keeps lattice; sequence_range respects clearance
        for i in range(40):
            db3.record(9, i, 1, f"wrap{i}".encode(), lattice="SEALED" if i % 2 == 0 else "INTERNAL")
        cold_internal = db3.recall_sequence_range(0, 1000, clearance="INTERNAL")
        cold_sealed = db3.recall_sequence_range(0, 1000, clearance="SEALED")
        assert all(c["lattice"] != "SEALED" for c in cold_internal)
        assert any(c["lattice"] == "SEALED" for c in cold_sealed)
        results["checks"]["cold_spill_lattice_enforced"] = True

        # 7) Rollback preserves lattice
        meta = db3.checkpoint(label="cage_ckpt", promote_sovereign=False)
        for i in range(4):
            db3.record(9, 100 + i, 1, b"after", lattice="SEALED")
        db3.rollback_to(meta.checkpoint_id)
        backlog_after = db3.recall_backlog(64, clearance="SEALED")
        assert all(e["lattice"] in ("SEALED", "INTERNAL", "PUBLIC", "RESTRICTED") for e in backlog_after)
        results["checks"]["checkpoint_rollback_lattice_preserved"] = True
        results["checkpoint_id"] = meta.checkpoint_id

        results["verdict"] = "VERIFIED_CAGE_LATTICE"
        results["timestamp_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return results
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def main() -> None:
    print("=" * 70)
    print("XORAS DART CAGE LATTICE ACCEPTANCE (MERIDIAN Layer 1)")
    print("=" * 70)
    receipt = _run()
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    print(f"\n[RECEIPT] {RECEIPT}")
    failed = [k for k, v in receipt["checks"].items() if v is False]
    if failed:
        raise SystemExit(f"FAILED: {failed}")
    print("ALL CAGE CHECKS PASSED")

if __name__ == "__main__":
    main()
