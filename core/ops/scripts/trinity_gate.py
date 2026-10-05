#!/usr/bin/env python3
"""
Layer-7 Trinity Gate Engine (Adversarial Multi-Agent Governance Integration)
-----------------------------------------------------------------------------
Invokes the Layer-7 Adversarial Trinity Tribunal (`adversarial_trinity_tribunal.py`) to enforce
real multi-agent cross-examination across Maxx (Bare-Metal), Clara (Human Protection),
and Vance (Cryptography). Eliminates canned audio placeholders and rubber-stamp compliance.
"""

import sys
import os
import subprocess
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
TRIBUNAL_SCRIPT = ROOT / "core" / "ops" / "scripts" / "adversarial_trinity_tribunal.py"

def main():
    if len(sys.argv) < 2:
        print("Usage: trinity_gate.py <command_to_verify> [target_files...]")
        sys.exit(1)

    full_cmd = " ".join(sys.argv[1:])

    if not TRIBUNAL_SCRIPT.is_file():
        print(f"❌ Error: Adversarial Tribunal script missing at {TRIBUNAL_SCRIPT}")
        sys.exit(1)

    # Dispatch to multi-agent adversarial tribunal
    args = [sys.executable, str(TRIBUNAL_SCRIPT), full_cmd]
    res = subprocess.run(args)
    if res.returncode != 0:
        print(f"❌ TRINITY GATE REJECTED: Command '{full_cmd}' failed multi-agent tribunal cross-examination.")
        sys.exit(1)

    # Execute authorized command
    print(f"🚀 EXECUTING AUTHORIZED COMMAND: {full_cmd}")
    exec_res = subprocess.run(full_cmd, shell=True)
    sys.exit(exec_res.returncode)

if __name__ == "__main__":
    main()
