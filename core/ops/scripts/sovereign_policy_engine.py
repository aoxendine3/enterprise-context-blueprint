#!/usr/bin/env python3
"""
Stage 1: Sovereign Policy Engine (Intent Filter)
------------------------------------------------
Author: Lead 9 Council / Xoras Systems Architect Board
Date: October 4, 2026

The 3-Stage Order of Protection:
- STAGE 1: Policy Engine (Intent Filter) -> Sits in FRONT of everything. Decides if action is permitted.
- STAGE 2: The Gate (Execution Filter)   -> Trinity Gate, AST Inspector, MARS 4-Layer Vetoes.
- STAGE 3: The Witness (Verification)    -> Native Zig Witness, Merkle Root Recomputation, Receipt-as-Node.

If Stage 1 (Policy) rejects an action, execution halts immediately with Exit Code 10.
Neither Stage 2 (Gate) nor Stage 3 (Witness) are ever invoked.
"""

import sys
import os
import time
import json
import re
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
POLICY_MANIFEST = ROOT / "ops" / "policy" / "sovereign_policy_manifest.json"

def log_policy(msg: str):
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    print(f"[{ts}] {msg}")

def evaluate_stage1_policy(cmd_args: list) -> tuple[bool, str]:
    if not POLICY_MANIFEST.is_file():
        return False, "POLICY_MANIFEST_MISSING"

    policy = json.loads(POLICY_MANIFEST.read_text(encoding="utf-8")).get("intent_filter_rules", {})
    cmd_str = " ".join(cmd_args)

    if not cmd_args:
        return True, "EMPTY_COMMAND_AUTHORIZED"

    base_cmd = os.path.basename(cmd_args[0])
    whitelist = policy.get("command_whitelist", [])
    prohibited = policy.get("prohibited_command_patterns", [])
    blocked_paths = policy.get("sensitive_data_protection", {}).get("blocked_path_patterns", [])

    # 1. Subshell Command Substitution & Injection Check
    subshell_patterns = [r"\$\(.*\)", r"`.*`", r";", r"&&", r"\|\|"]
    for sp in subshell_patterns:
        if re.search(sp, cmd_str):
            # Inspect embedded commands in subshell
            subshell_match = re.findall(r"\$\((.*?)\)|`(.*?)`", cmd_str)
            for tuple_match in subshell_match:
                sub_cmd = (tuple_match[0] or tuple_match[1]).strip()
                sub_base = os.path.basename(sub_cmd.split()[0]) if sub_cmd.split() else ""
                if sub_base not in whitelist:
                    return False, f"POLICY_VIOLATION_UNAUTHORIZED_SUBSHELL_INJECTION: Subshell command '{sub_base}' is not in policy whitelist"

    # 2. Prohibited Command Pattern Check
    for pattern in prohibited:
        if pattern in cmd_str:
            return False, f"POLICY_VIOLATION_PROHIBITED_PATTERN: Pattern '{pattern}' is explicitly banned by policy"

    # 3. Sensitive Path Boundary Check
    for bpath in blocked_paths:
        if bpath in cmd_str:
            return False, f"POLICY_VIOLATION_SENSITIVE_PATH: Access to '{bpath}' is strictly prohibited"

    # 4. Base Command Whitelist Check
    if base_cmd not in whitelist:
        return False, f"POLICY_VIOLATION_UNWHITELISTED_COMMAND: Base command '{base_cmd}' is not in policy whitelist"

    return True, f"STAGE_1_POLICY_AUTHORIZED: Command '{base_cmd}' permitted"

def main():
    log_policy("=" * 80)
    log_policy("  STAGE 1: SOVEREIGN POLICY ENGINE (INTENT FILTER)")
    log_policy("==========================================================================")

    cmd_args = sys.argv[1:]
    permitted, reason = evaluate_stage1_policy(cmd_args)

    if permitted:
        log_policy(f"✅ STAGE 1 PASSED: {reason}")
        sys.exit(0)
    else:
        log_policy(f"❌ STAGE 1 REJECTED (FAIL-CLOSED): {reason}")
        log_policy("  └─ Action halted at Stage 1 Intent Filter. Gate (Stage 2) & Witness (Stage 3) bypassed.")
        sys.exit(10) # Exit code 10 = Policy Intent Rejection

if __name__ == "__main__":
    main()
