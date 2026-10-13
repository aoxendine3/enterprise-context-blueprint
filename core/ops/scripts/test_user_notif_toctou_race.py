#!/usr/bin/env python3
"""
Empirical Verification & Demonstration Runner:
SECCOMP_RET_USER_NOTIF Time-of-Check to Time-of-Use (TOCTOU) Memory Race Exploit
"""

import subprocess
import json
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
BIN_PATH = REPO_ROOT / "tests" / "exploits" / "demonstrate_user_notif_toctou"

def run_toctou_demo(iterations: int = 10000):
    if not BIN_PATH.exists():
        # Compile if missing
        src_path = BIN_PATH.with_suffix(".c")
        subprocess.run(["clang", "-O2", "-lpthread", str(src_path), "-o", str(BIN_PATH)], check=True)

    res = subprocess.run([str(BIN_PATH), str(iterations)], capture_output=True, text=True, check=True)
    print(res.stdout)

    # Parse stdout for receipt
    exploit_rate = 0.0
    slipped_count = 0
    for line in res.stdout.splitlines():
        if "TOCTOU Races Slipped Past Supervisor" in line:
            slipped_count = int(line.split(":")[-1].strip())
        if "Exploit Success Rate" in line:
            exploit_rate = float(line.split(":")[-1].replace("%", "").strip())

    receipt = {
        "timestamp": time.time(),
        "iterations": iterations,
        "supervisor_model": "SECCOMP_RET_USER_NOTIF / USER_SPACE_INSPECTION (Sandlock-Style)",
        "slipped_races_count": slipped_count,
        "exploit_success_rate_percent": exploit_rate,
        "vulnerability_proven": (slipped_count > 0),
        "upgp_contrast": "In-Kernel Atomic BPF Whitelist (SCMP_ACT_KILL) with 0 Userland TOCTOU Window"
    }

    receipt_path = REPO_ROOT / "memory" / "catch_log" / "toctou_exploit_receipt.json"
    with open(receipt_path, "w") as f:
        json.dump(receipt, f, indent=2)

    print(f"[+] Audit Receipt Recorded to {receipt_path}")
    return receipt

if __name__ == "__main__":
    run_toctou_demo()
