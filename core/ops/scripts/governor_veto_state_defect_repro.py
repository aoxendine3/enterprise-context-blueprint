#!/usr/bin/env python3
"""
Governor veto regression: signed semantic poison must be refused
================================================================

This script is the standing regression for the defect found on 2026-11-15.
It is a detector, not a gate: exit 0 means the attack is **blocked**, exit 1
means it reproduced.

Attack shape (the original defect)
----------------------------------
1. Honest baseline: ``canonical_mass = 18432.0``.
2. Insider writes ``666.666`` with ``explicit_supersede=True`` at the same
   timestamp. Row id ``sha256(agent:key:timestamp)`` collided, and
   ``INSERT OR REPLACE`` overwrote the honest row.
3. Unannounced poison afterwards was scored 0.95 "identical confirmation"
   because ``score_supersession`` used ``fetchone()`` with no ordering.

Post-fix invariants asserted here
---------------------------------
- The honest baseline survives; no poison row is stored.
- Same-timestamp supersede is vetoed (row ids no longer collide).
- A non-authorised seat cannot claim supersession.
- An authorised seat still cannot bypass the Poincaré gate.
- Repeated unannounced poison is vetoed every time.
- The authoritative read is the honest row, deterministically.

Everything runs against a temporary database. The live
``.sovereign/hippocampus/governed_memory.db`` is never opened.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sqlite3
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone

REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "core" / "ops" / "memory"))

import governed_memory_consolidation_engine as engine  # noqa: E402

TRUE_MASS = "18432.0"
POISON = "666.666"


def run() -> dict:
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="gov_veto_regression_"))
    engine.GOVERNANCE_DB = tmp / "governed_memory.db"
    engine.GOVERNANCE_JSONL = tmp / "receipts.jsonl"
    engine.GOVERNANCE_LOG = tmp / "gauntlet.log"

    gov = engine.GovernedMemoryGovernor()

    source = tmp / "signed_telemetry_source.json"
    source.write_text(json.dumps({"sensor": "cfd", "verified_mass": 18432.0}))
    merkle = hashlib.sha256(source.read_bytes()).hexdigest()

    t0 = datetime.now(timezone.utc).replace(microsecond=0)
    steps = []

    def call(label, value, when, supersede=False, agent="clara"):
        res = gov.evaluate_write_candidate(
            agent_id=agent,
            key="canonical_mass",
            value=value,
            source_path=str(source),
            merkle_hash=merkle,
            timestamp_iso=when.isoformat(),
            target_capsule=agent,
            explicit_supersede=supersede,
        )
        steps.append(
            {
                "step": label,
                "agent": agent,
                "value": value,
                "timestamp": when.isoformat(),
                "explicit_supersede": supersede,
                "status": res["status"],
                "accepted": res["accepted"],
                "governance_score": res["governance_score"],
                "supersession_axis": res["axes"]["Supersession"],
                "gate_decision": res["poincare"]["decision"],
                "gate_reason": res["poincare"]["reason"],
                "gate_distance": res["poincare"]["distance"],
                "veto_reasons": res["veto_reasons"],
            }
        )
        return res

    # 1. Honest baseline. No supersede claim: this is an anchor.
    call("honest_baseline", TRUE_MASS, t0)
    # 2. Same-timestamp signed poison, insider supersede claim.
    call("poison_explicit_supersede_same_ts", POISON, t0, supersede=True)
    # 3. Unannounced poison, repeatedly.
    for i in range(1, 4):
        call(f"unannounced_poison_t+{i}m", POISON, t0 + timedelta(minutes=i))
    # 4. Authorised seat (maxx) still may not bypass the gate.
    call("authorised_supersede_poison", POISON, t0 + timedelta(minutes=4), supersede=True, agent="maxx")
    # 5. Honest restatement is accepted (identical confirmation, S=0.95).
    call("honest_restatement", TRUE_MASS, t0 + timedelta(minutes=5))

    conn = sqlite3.connect(engine.GOVERNANCE_DB)
    rows = conn.execute(
        "SELECT value, status, created_at FROM memory_records "
        "WHERE key='canonical_mass' ORDER BY rowid"
    ).fetchall()
    conn.close()

    accepted_poison = [s for s in steps if s["value"] == POISON and s["accepted"]]
    stored_poison = [r for r in rows if r[0] == POISON]
    honest_rows = [r for r in rows if r[0] == TRUE_MASS and r[1] == "ACCEPTED"]
    authoritative = gov.latest_accepted("canonical_mass")

    blocked = (
        not accepted_poison
        and not stored_poison
        and bool(honest_rows)
        and authoritative is not None
        and authoritative["value"] == TRUE_MASS
    )

    return {
        "steps": steps,
        "defect": {
            "reproduced": not blocked,
            "blocked": blocked,
            "unannounced_poison_accepted": len(accepted_poison),
            "poison_rows_stored": len(stored_poison),
            "honest_rows_accepted": len(honest_rows),
            "rows_after": rows,
            "authoritative_value": authoritative["value"] if authoritative else None,
            "same_timestamp_row_count": len([r for r in rows if r[2] == t0.isoformat()]),
        },
    }


def main() -> int:
    result = run()
    receipt = {
        "standard": "XORAS-GOVERNOR-SEMANTIC-VETO-REGRESSION-v2.0",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": (
            "Signed semantic poison is refused by the Poincare gate on every path: "
            "same-timestamp supersede, non-authorised supersede, authorised supersede, "
            "and repeated unannounced writes. The honest baseline survives and remains "
            "the authoritative value."
        ),
        "isolation": "temporary database only; live governed_memory.db untouched",
        **result,
    }
    out = REPO / "memory" / "catch_log" / "governor_veto_state_defect_receipt.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

    print(f"{'step':<40}{'agent':<8}{'status':<26}{'gate':<8}{'d_H':>9}{'S':>6}")
    for s in result["steps"]:
        d = s["gate_distance"]
        d_txt = f"{d:.4f}" if isinstance(d, (int, float)) else "-"
        print(
            f"{s['step']:<40}{s['agent']:<8}{s['status']:<26}"
            f"{s['gate_decision']:<8}{d_txt:>9}{s['supersession_axis']:>6.2f}"
        )
    defect = result["defect"]
    print(f"\nrows after run: {defect['rows_after']}")
    print(f"unannounced poison accepted: {defect['unannounced_poison_accepted']}")
    print(f"poison rows stored: {defect['poison_rows_stored']}")
    print(f"authoritative value: {defect['authoritative_value']}")
    print(f"defect blocked: {defect['blocked']}")
    print(f"receipt: {out}")
    return 0 if defect["blocked"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
