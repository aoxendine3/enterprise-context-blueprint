#!/usr/bin/env python3
"""
Reproduce and receipt the Governed Memory contradiction-veto defect
===================================================================

The hard veto in ``GovernedMemoryGovernor`` is supposed to reject a signed
payload that contradicts an already-accepted value. It does — on a fresh
database, first write. It does not survive its own history.

Two mechanisms defeat it:

1. Row identity is ``sha256(agent:key:timestamp)``. An insider write with
   ``explicit_supersede=True`` at the same timestamp as the honest write
   produces the same id, so ``INSERT OR REPLACE`` overwrites the honest
   baseline with the poisoned value.
2. ``score_supersession`` reads ``SELECT value ... WHERE key = ?`` with
   ``fetchone()`` and no ordering. Once more than one accepted row exists for
   a key, which value counts as "the existing state" is arbitrary — and the
   oldest row (often the poison) is returned.

Net effect: after one accepted supersede, unannounced poison of the same value
is scored as an "identical confirmation" (S=0.95) and ACCEPTED.

This script runs entirely against a temporary database. It never touches the
live ``.sovereign/hippocampus/governed_memory.db``. It writes
``memory/catch_log/governor_veto_state_defect_receipt.json`` and exits 0 when
the defect is reproduced (this is a detector, not a gate).
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sqlite3
import sys
import tempfile
import time

REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "core" / "ops" / "memory"))

import governed_memory_consolidation_engine as engine  # noqa: E402


def run() -> dict:
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="gov_veto_repro_"))
    engine.GOVERNANCE_DB = tmp / "governed_memory.db"
    gov = engine.GovernedMemoryGovernor()

    source = tmp / "signed_telemetry_source.json"
    source.write_text(json.dumps({"sensor": "cfd", "verified_mass": 18432.0}))
    merkle = hashlib.sha256(source.read_bytes()).hexdigest()

    t0 = "2026-11-15T00:00:00Z"
    steps = []

    def call(label, value, ts, supersede=False):
        res = gov.evaluate_write_candidate(
            agent_id="clara",
            key="canonical_mass",
            value=value,
            source_path=str(source),
            merkle_hash=merkle,
            timestamp_iso=ts,
            target_capsule="clara",
            explicit_supersede=supersede,
        )
        steps.append(
            {
                "step": label,
                "value": value,
                "timestamp": ts,
                "explicit_supersede": supersede,
                "status": res["status"],
                "accepted": res["accepted"],
                "governance_score": res["governance_score"],
                "supersession_axis": res["axes"]["Supersession"],
                "veto_reasons": res["veto_reasons"],
            }
        )
        return res

    # 1. Honest baseline.
    call("honest_baseline", "18432.0", t0, supersede=True)
    # 2. Insider supersede at the SAME timestamp -> same row id -> overwrite.
    call("signed_poison_explicit_supersede_same_ts", "666.666", t0, supersede=True)
    # 3. Unannounced poison afterwards.
    call("unannounced_poison_t1", "666.666", "2026-11-15T00:01:00Z")
    call("unannounced_poison_t2", "666.666", "2026-11-15T00:02:00Z")

    conn = sqlite3.connect(engine.GOVERNANCE_DB)
    rows = conn.execute(
        "select value, status, created_at from memory_records where key='canonical_mass' order by rowid"
    ).fetchall()
    conn.close()

    accepted_unannounced = [s for s in steps if s["step"].startswith("unannounced") and s["accepted"]]
    defect = {
        "same_timestamp_row_count": len([r for r in rows if r[2] == t0]),
        "honest_row_survived_supersede": any(r[0] == "18432.0" for r in rows),
        "rows_after": rows,
        "unannounced_poison_accepted": len(accepted_unannounced),
        "reproduced": bool(accepted_unannounced) and not any(r[0] == "18432.0" for r in rows),
    }
    return {"steps": steps, "defect": defect}


def main() -> int:
    result = run()
    receipt = {
        "standard": "XORAS-GOVERNOR-VETO-STATE-DEFECT-v1.0",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": (
            "Contradiction veto is defeated by same-timestamp row overwrite and "
            "unordered per-key fetch; unannounced poison is accepted after one supersede."
        ),
        "isolation": "temporary database only; live governed_memory.db untouched",
        **result,
    }
    out = REPO / "memory" / "catch_log" / "governor_veto_state_defect_receipt.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

    print(f"{'step':<44}{'status':<26}{'score':>7}{'S':>7}")
    for s in result["steps"]:
        print(f"{s['step']:<44}{s['status']:<26}{s['governance_score']:>7.3f}{s['supersession_axis']:>7.2f}")
    print(f"\nrows after run: {result['defect']['rows_after']}")
    print(f"unannounced poison accepted: {result['defect']['unannounced_poison_accepted']}")
    print(f"defect reproduced: {result['defect']['reproduced']}")
    print(f"receipt: {out}")
    return 0 if result["defect"]["reproduced"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
