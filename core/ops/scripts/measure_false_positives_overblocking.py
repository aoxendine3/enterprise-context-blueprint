#!/usr/bin/env python3
"""
False Positive & Overblocking Measurement Harness
-------------------------------------------------
Author: Lead 9 Council / Xoras Systems Architect Board
Date: October 4, 2026

Fulfills the Overblocking Measurement Invariant:
"A gate that halts on everything is a brick, not a safeguard."
Executes legitimate, authorized operational commands through the Trinity Gate
and measures the False Positive Rate (FPR) and Overblocking Ratio (OBR).
"""

import sys
import os
import time
import json
import subprocess
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
RUN_TRINITY = ROOT / "ops" / "scripts" / "run_with_trinity.sh"
AUDITS_DIR = ROOT / "docs" / "audits"

# List of 20 legitimate, valid operational commands across routine developer workloads that must pass the gate
AUTHORIZED_OPERATIONAL_COMMANDS = [
    {"id": "VALID-01", "cmd": "git status", "target": None},
    {"id": "VALID-02", "cmd": "git log -n 1", "target": None},
    {"id": "VALID-03", "cmd": "git diff", "target": None},
    {"id": "VALID-04", "cmd": "cat AGENTS.md", "target": "AGENTS.md"},
    {"id": "VALID-05", "cmd": "ls -la docs/audits/", "target": "docs/audits"},
    {"id": "VALID-06", "cmd": "grep -r Sovereign ops/policy/", "target": None},
    {"id": "VALID-07", "cmd": "find docs/ -name *.md", "target": None},
    {"id": "VALID-08", "cmd": "head -n 5 AGENTS.md", "target": "AGENTS.md"},
    {"id": "VALID-09", "cmd": "tail -n 5 AGENTS.md", "target": "AGENTS.md"},
    {"id": "VALID-10", "cmd": "pwd", "target": None},
    {"id": "VALID-11", "cmd": "whoami", "target": None},
    {"id": "VALID-12", "cmd": "uptime", "target": None},
    {"id": "VALID-13", "cmd": "uname -a", "target": None},
    {"id": "VALID-14", "cmd": "df -h", "target": None},
    {"id": "VALID-15", "cmd": "wc -l AGENTS.md", "target": "AGENTS.md"},
    {"id": "VALID-16", "cmd": "echo Hello_Sovereign_Gate", "target": None},
    {"id": "VALID-17", "cmd": "python3 ops/scripts/hardware_hsm_signing_bridge.py", "target": "ops/scripts/hardware_hsm_signing_bridge.py"},
    {"id": "VALID-18", "cmd": "python3 core/ops/scripts/monotonic_tsa_time_verifier.py", "target": "core/ops/scripts/monotonic_tsa_time_verifier.py"},
    {"id": "VALID-19", "cmd": "python3 ops/scripts/fail_closed_remediation.py", "target": "ops/scripts/fail_closed_remediation.py"},
    {"id": "VALID-20", "cmd": "python3 core/ops/scripts/repair_lineage_dag.py", "target": "core/ops/scripts/repair_lineage_dag.py"},
]

def ensure_executable_permissions():
    """Ensure all legitimate test targets have executable permissions to avoid bare-metal VETOs."""
    for item in AUTHORIZED_OPERATIONAL_COMMANDS:
        if item["target"]:
            p = ROOT / item["target"]
            if p.is_file() and p.suffix in [".sh", ".py"]:
                os.chmod(p, 0o755)

def run_false_positive_gauntlet() -> dict:
    print("=" * 80)
    print("  FALSE POSITIVE & OVERBLOCKING MEASUREMENT HARNESS")
    print("  Measuring Gate Availability vs Legitimate Operational Workloads")
    print("=" * 80)

    ensure_executable_permissions()
    results = []
    total = len(AUTHORIZED_OPERATIONAL_COMMANDS)
    false_positives = 0

    for item in AUTHORIZED_OPERATIONAL_COMMANDS:
        cmd_str = item["cmd"]
        cid = item["id"]
        print(f"\n[{cid}] Executing Legitimate Command: '{cmd_str}'")
        start_t = time.time()

        res = subprocess.run([str(RUN_TRINITY)] + cmd_str.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        duration = round(time.time() - start_t, 4)

        # A false positive occurs if a legitimate command is rejected (returncode != 0)
        is_false_positive = res.returncode != 0
        if is_false_positive:
            false_positives += 1
            print(f"   ❌ FALSE POSITIVE REJECTION (Exit Code: {res.returncode})")
            print(f"      Stdout: {res.stdout[:200]}")
        else:
            print(f"   ✅ AUTHORIZED PASSED CLEANLY (Exit Code: 0)")

        results.append({
            "command_id": cid,
            "command_str": cmd_str,
            "exit_code": res.returncode,
            "false_positive": is_false_positive,
            "duration_sec": duration
        })

    fpr = (false_positives / total) * 100.0
    overblocking_ratio = false_positives / total

    print("\n" + "=" * 80)
    print(f"  OVERBLOCKING MEASUREMENT SUMMARY")
    print(f"  Total Valid Workloads Tested: {total}")
    print(f"  Passed Workloads:            {total - false_positives}")
    print(f"  False Positive Rejections:   {false_positives}")
    print(f"  False Positive Rate (FPR):   {fpr:.2f}%")
    print(f"  Overblocking Ratio (OBR):    {overblocking_ratio:.4f}")
    print("=" * 80)

    report_data = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_tested": total,
        "passed": total - false_positives,
        "false_positives": false_positives,
        "false_positive_rate_pct": fpr,
        "overblocking_ratio": overblocking_ratio,
        "results": results
    }

    AUDITS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = AUDITS_DIR / "FALSE_POSITIVE_OVERBLOCKING_RECEIPT.json"
    out_file.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
    print(f"\n📄 Saved Overblocking Receipt: {out_file}")

    barn_file = ROOT / "barn" / "receipts" / "FALSE_POSITIVE_OVERBLOCKING_RECEIPT.json"
    if barn_file.parent.exists():
        import shutil
        shutil.copy2(out_file, barn_file)
        print(f"📦 Synced Barn Vault Copy:     {barn_file}\n")

    return report_data

if __name__ == "__main__":
    run_false_positive_gauntlet()
