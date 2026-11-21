#!/usr/bin/env python3
"""
DAXX SSOT FULL AUDIT RUNNER — REWIRED (Vance remediation, 2026-11-20).

PREVIOUS VERSION WAS THEATER: all 7 pillars hardcoded "status": "PASS" and
printed fabricated claims (ASAN/TSAN clean, 100% unanimous consensus, zero
leaks) it never executed. Any receipt from it was void.

THIS VERSION calls REAL gates, records their ACTUAL exit codes and output,
and FAILS CLOSED if any critical gate fails. No hardcoded verdicts.
"""
import os
import sys
import json
import time
import subprocess
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
RECEIPT = ROOT / "memory/catch_log/DAXXCO_SSOT_FULL_AUDIT_RECEIPT.json"
PY = ROOT / ".venv/bin/python"
if not PY.exists():
    PY = Path("python3")

# Each pillar maps to a REAL, executable check. critical=True → fail closed.
PILLARS = [
    # reality_gate MUST run first: it writes REALITY_GATE_RECEIPT.json, which
    # the wire audit below reads. Running the auditor first created a circular
    # stale-receipt dependency (it failed on the PREVIOUS run's verdict).
    ("reality_gate", "Full 9-gate reality verification",
     ["bash", str(ROOT / "ops/scripts/reality_gate.sh")], True),
    ("judge_and_witness_gate", "Witness + provenance gates",
     [str(PY), str(ROOT / "ops/scripts/ssot_wire_audit.py")], True),
    ("dual_witness", "Independent Zig + Python consensus",
     ["bash", str(ROOT / "core/ops/scripts/dual_witness_gate.sh")], True),
    ("dart_cage", "DART cage lattice 7/7",
     [str(PY), str(ROOT / "tests/test_dart_cage_lattice.py")], True),
    ("side_channel", "UPGP timing side-channel 4 axes",
     ["node", "--expose-gc", str(ROOT / "core/ops/scripts/test_side_channel_verification.cjs")], True),
    ("z3_cage", "Z3 cage_containment UNSAT",
     ["bash", "-lc", "cd " + str(ROOT) + " && z3 core/ops/security/cage_containment.smt2 2>/dev/null | grep -q unsat"], False),
    ("identity_scope", "Citizen card seal + read-only scope",
     [str(PY), str(ROOT / "ops/security/identity_scope_guard.py"), "--agent", "maxx"], False),
]


def run_pillar(name, label, cmd, critical):
    started = time.time()
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=900)
        rc = proc.returncode
        out = (proc.stdout or "")[-4000:]
        err = (proc.stderr or "")[-2000:]
    except subprocess.TimeoutExpired:
        rc, out, err = -99, "TIMEOUT", "gate exceeded 900s"
    except FileNotFoundError as e:
        rc, out, err = -98, "", str(e)
    status = "PASS" if rc == 0 else "FAIL"
    return {
        "status": status,
        "critical": critical,
        "exit_code": rc,
        "duration_s": round(time.time() - started, 2),
        "command": " ".join(cmd),
        "output_tail": out,
        "stderr_tail": err,
    }


def main():
    print("=" * 70)
    print("DAXX SSOT FULL AUDIT — REAL GATE EXECUTION (fail-closed)")
    print(f"Target: {ROOT}")
    print(f"Timestamp: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
    print("=" * 70)

    pillars = {}
    for key, label, cmd, critical in PILLARS:
        print(f"\n[{list(PILLARS).index((key, label, cmd, critical)) + 1}/{len(PILLARS)}] {label}...")
        pillars[key] = run_pillar(key, label, cmd, critical)
        p = pillars[key]
        print(f"    {p['status']}  exit={p['exit_code']}  {p['duration_s']}s")

    critical_fail = any(p["status"] == "FAIL" and p["critical"] for p in pillars.values())
    any_fail = any(p["status"] == "FAIL" for p in pillars.values())
    verdict = "DAXX_AUDIT_FAIL" if critical_fail else (
        "DAXX_AUDIT_DEGRADED" if any_fail else "DAXX_AUDIT_PASS")

    receipt = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "verdict": verdict,
        "critical_fail": critical_fail,
        "honesty": "real gate exit codes; no hardcoded verdicts; fail-closed",
        "pillars": pillars,
    }
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(receipt, indent=2))

    print("\n" + "=" * 70)
    print(f"VERDICT: {verdict}")
    print(f"Receipt: {RECEIPT}")
    print("=" * 70)
    return 1 if critical_fail else 0


if __name__ == "__main__":
    sys.exit(main())
