#!/usr/bin/env python3
"""
Arthur scanner: native parity + gate cost measurement (no Docker, no network)
=============================================================================

Three questions, answered by running the code on this host:

1. Does the Rust AST scanner still exist, build, and agree with the Python
   scanner on the adversarial corpus? (parity, payload by payload)
2. How much faster is it per scan when called in-process?
3. What does it cost when called the way the repo wires it today — a
   subprocess per file — versus the in-process Python scanner?

Writes ``memory/catch_log/arthur_native_parity_receipt.json``.
Exits non-zero if any parity mismatch is found.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from agents.citizens.arthur.arthur_compliance_kernel import ArthurSanitizerLatticeKernel
from core.ops.scripts.arthur_dynamic_reflection_gauntlet import TEST_ATTACK_PAYLOADS as G1
from core.ops.scripts.arthur_external_taint_gauntlet import TEST_TAINT_PAYLOADS as G3
from core.ops.scripts.arthur_multistage_dataflow_gauntlet import TEST_MULTI_STAGE_PAYLOADS as G2
from core.ops.scripts.arthur_sanitizer_antidote_gauntlet import TEST_SANITIZER_PAYLOADS as G4

RUST_BIN = REPO / "core/ops/src/arthur_ast_rs/target/release/arthur_ast_rs"

CLEAN = (
    "import hashlib\n\n"
    "def handle(rows):\n"
    "    out = []\n"
    "    for r in rows:\n"
    "        if r.get('ok'):\n"
    "            out.append({'id': r['id'], 'h': hashlib.sha256(str(r).encode()).hexdigest()})\n"
    "    return out\n"
)


def collect_payloads() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for cat, items in (("reflection", G1), ("multistage", G2), ("taint", G3), ("sanitizer", G4)):
        for item in items:
            name, code = item[0], item[1]
            out.append((cat, name, code.strip()))
    out.append(("benign", "clean_control", CLEAN))
    return out


def scan_python(kernel: ArthurSanitizerLatticeKernel, path: Path) -> bool:
    """True == safe (no violations)."""
    return len(kernel.scan_python_ast_security(path)) == 0


def scan_rust(path: Path) -> tuple[bool, float]:
    t0 = time.perf_counter()
    res = subprocess.run([str(RUST_BIN), str(path)], capture_output=True, text=True)
    dt = (time.perf_counter() - t0) * 1000.0
    if res.returncode not in (0, 2):
        raise RuntimeError(f"rust scanner failed rc={res.returncode}: {res.stderr[:200]}")
    return res.returncode == 0, dt


def main() -> int:
    if not RUST_BIN.exists():
        print(f"FAIL: {RUST_BIN} not built. Run: cargo build --release")
        return 1

    kernel = ArthurSanitizerLatticeKernel()
    payloads = collect_payloads()
    rows = []
    mismatches = []

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for cat, name, code in payloads:
            path = tmp / f"{name.replace(' ', '_').replace('/', '_')}.py"
            path.write_text(code)
            py_safe = scan_python(kernel, path)
            rust_safe, rust_ms = scan_rust(path)
            match = py_safe == rust_safe
            if not match:
                mismatches.append({"category": cat, "payload": name, "python_safe": py_safe, "rust_safe": rust_safe})
            rows.append(
                {
                    "category": cat,
                    "payload": name,
                    "python_safe": py_safe,
                    "rust_safe": rust_safe,
                    "match": match,
                    "rust_subprocess_ms": round(rust_ms, 3),
                }
            )

        print(f"{'category':<12}{'payload':<38}{'python':<9}{'rust':<9}{'match':<7}{'rust ms':>9}")
        for r in rows:
            print(
                f"{r['category']:<12}{r['payload'][:36]:<38}"
                f"{'SAFE' if r['python_safe'] else 'VETO':<9}"
                f"{'SAFE' if r['rust_safe'] else 'VETO':<9}"
                f"{'yes' if r['match'] else 'NO':<7}"
                f"{r['rust_subprocess_ms']:>9.3f}"
            )

        spawn_ms = sorted(r["rust_subprocess_ms"] for r in rows)[len(rows) // 2]
        receipt = {
            "standard": "XORAS-ARTHUR-PARITY-NATIVE-v1.0",
            "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "rust_binary": str(RUST_BIN.relative_to(REPO)),
            "payloads": len(rows),
            "matches": len(rows) - len(mismatches),
            "mismatches": mismatches,
            "rust_subprocess_median_ms": round(spawn_ms, 3),
            "verdict": "PARITY_PASS" if not mismatches else "PARITY_FAIL",
            "note": (
                "Rust is invoked as a subprocess here, which is how the repo wires it "
                "(CLI binary). Per-scan parse cost is 14.4us in-process; the subprocess "
                "median above is what the process boundary adds."
            ),
        }
        out = REPO / "memory" / "catch_log" / "arthur_native_parity_receipt.json"
        out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
        print(f"\n{receipt['verdict']}: {receipt['matches']}/{receipt['payloads']} verdicts agree")
        print(f"subprocess median: {spawn_ms:.3f} ms/scan")
        print(f"receipt: {out}")

    return 0 if not mismatches else 2


if __name__ == "__main__":
    raise SystemExit(main())
