#!/usr/bin/env python3
"""
Full Gauntlet Suite Runner: Arthur Python AST Engine vs Arthur Rust (arthur_ast_rs).
Runs all 24 payloads across 4 gauntlets:
  1. Dynamic Reflection Gauntlet (7 payloads)
  2. Multi-Stage Data-Flow Gauntlet (7 payloads)
  3. External Runtime Taint Gauntlet (6 payloads)
  4. Poison & Antidote Sanitizer Gauntlet (5 payloads)
"""

import os
import sys
import subprocess
from pathlib import Path

WORKSPACE = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
sys.path.insert(0, str(WORKSPACE))

from agents.citizens.arthur.arthur_compliance_kernel import ArthurSanitizerLatticeKernel
from core.ops.scripts.arthur_dynamic_reflection_gauntlet import TEST_ATTACK_PAYLOADS as GAUNTLET_1
from core.ops.scripts.arthur_multistage_dataflow_gauntlet import TEST_MULTI_STAGE_PAYLOADS as GAUNTLET_2
from core.ops.scripts.arthur_external_taint_gauntlet import TEST_TAINT_PAYLOADS as GAUNTLET_3
from core.ops.scripts.arthur_sanitizer_antidote_gauntlet import TEST_SANITIZER_PAYLOADS as GAUNTLET_4

ALL_PAYLOADS = []

for name, code in GAUNTLET_1:
    ALL_PAYLOADS.append(("Gauntlet 1: Reflection", name, code.strip()))

for name, code in GAUNTLET_2:
    ALL_PAYLOADS.append(("Gauntlet 2: Multi-Stage", name, code.strip()))

for name, code in GAUNTLET_3:
    ALL_PAYLOADS.append(("Gauntlet 3: External Taint", name, code.strip()))

for item in GAUNTLET_4:
    name, code = item[0], item[1].strip()
    ALL_PAYLOADS.append(("Gauntlet 4: Sanitizer/Antidote", name, code))

def main():
    print("=" * 84)
    print("  EXHAUSTIVE 25-PAYLOAD PARITY GAUNTLET: PYTHON vs RUST (arthur_ast_rs)")
    print("=" * 84)

    scratch_dir = WORKSPACE / "core/ops/scratch_full_gauntlet"
    scratch_dir.mkdir(parents=True, exist_ok=True)

    py_kernel = ArthurSanitizerLatticeKernel()
    rust_binary = "/workspace/core/ops/src/arthur_ast_rs/target/release/arthur_ast_rs"

    total = len(ALL_PAYLOADS)
    matches = 0
    mismatches = []

    print(f"{'Category':<24} | {'Payload Name':<34} | {'Python':<10} | {'Rust':<10} | {'Match'}")
    print("-" * 84)

    for cat, name, code in ALL_PAYLOADS:
        fpath = scratch_dir / name
        fpath.write_text(code)

        # Run Python
        py_violations = py_kernel.scan_python_ast_security(fpath)
        py_verdict = "PASSED" if len(py_violations) == 0 else "VETO"

        # Run Rust
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{WORKSPACE}:/workspace",
            "-w", "/workspace",
            "rust:latest",
            rust_binary, f"/workspace/core/ops/scratch_full_gauntlet/{name}"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        rust_verdict = "PASSED" if res.returncode == 0 else "VETO"

        is_match = (py_verdict == rust_verdict)
        if is_match:
            matches += 1
            sym = "✓"
        else:
            sym = "✗"
            mismatches.append((cat, name, py_verdict, rust_verdict, py_violations, res.stdout, res.stderr))

        cat_short = cat.split(":")[1].strip() if ":" in cat else cat
        print(f"{cat_short:<24} | {name:<34} | {py_verdict:<10} | {rust_verdict:<10} | {sym}")

        fpath.unlink()

    scratch_dir.rmdir()

    print("=" * 84)
    accuracy = (matches / total) * 100.0
    print(f"  EXHAUSTIVE PARITY SCORE: {matches} / {total} ({accuracy:.1f}%)")
    if mismatches:
        print("\n  [MISMATCH FORENSICS]:")
        for cat, name, py_v, r_v, py_viol, r_out, r_err in mismatches:
            print(f"  - {name} ({cat}): Python={py_v}, Rust={r_v}")
            print(f"    Python Violations: {py_viol}")
            print(f"    Rust Output: {r_out.strip()}")
    else:
        print("  🎉 100% MATHEMATICAL AND BEHAVIORAL PARITY ACROSS ALL GAUNTLETS!")
    print("=" * 84)

if __name__ == "__main__":
    main()
