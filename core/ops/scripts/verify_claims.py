#!/usr/bin/env python3
"""
CLAIMS GATE — fail-closed verification of report evidence at generation time.

Root-cause fix for reports that carry fabricated hashes, nonexistent evidence
files, and claims that contradict the scripts they cite. Any report that wants
to be treated as evidence must pass this gate BEFORE it is spoken, committed,
posted, or handed to another agent.

Checks, mechanically:
  1. Every SHA-256-looking token bound to a path on the same line is recomputed
     against the real file; prefix must match. (Mismatch = FAIL)
  2. Every backtick-quoted path that looks like a file must exist in the repo,
     the workspace, or Desktop/test. (Missing = FAIL)
  3. Known contradiction lint: a "no synthetic delays/mocks" claim is checked
     against the actual benchmark scripts for deliberate sleep() calls.
  4. "100% coverage" claims are checked against the real gate floor.

Usage:
  python3 core/ops/scripts/verify_claims.py REPORT.md [--json]
  python3 core/ops/scripts/verify_claims.py --self-test
"""

import argparse
import hashlib
import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
SEARCH_ROOTS = [ROOT, Path("/Users/ajoxendine68/Desktop/test")]
RECEIPT = ROOT / "memory/catch_log/CLAIM_VERIFICATION_RECEIPT.json"
HEX = re.compile(r"(?<![0-9a-f])([0-9a-f]{8,64})(?![0-9a-f])")
PATH = re.compile(r"`([^`\n]+\.(?:json|log|py|md|sh|png|mp4|txt|yaml|c|rs))`")
EXTS = {".json", ".log", ".py", ".md", ".sh", ".png", ".mp4", ".txt", ".yaml", ".c", ".rs"}


def resolve(name: str) -> Path | None:
    p = Path(name).expanduser()
    if p.is_absolute() and p.exists():
        return p
    for root in SEARCH_ROOTS:
        cand = root / name
        if cand.exists():
            return cand
    # try basename match at bounded depth for bare filenames
    if "/" not in name:
        for root in SEARCH_ROOTS:
            for cand in root.glob("**/" + name):
                return cand
    return None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lint_contradictions(text: str) -> list:
    hits = []
    low = text.lower()
    scripts = [ROOT / "scratch/full_ceiling_20261118/bench_rust_ffi_swarm.py",
               ROOT / "scratch/full_ceiling_20261118/run_full_ceiling.py"]
    sleeping = any(s.exists() and "time.sleep(0.0001" in s.read_text() for s in scripts)
    if sleeping and ("no synthetic" in low or "no mock data" in low or "without synthetic" in low):
        hits.append("CONTRADICTION: report denies synthetic delays but benchmarks call time.sleep(0.0001+)")
    if "100% unit test coverage" in low or "100% coverage" in low:
        gate = ROOT / "core/ops/scripts/verify_cockpit.sh"
        if gate.exists() and "80.0" in gate.read_text():
            hits.append("CONTRADICTION: report claims 100% coverage; actual enforced floor is 80%")
    return hits


def verify(text: str, source: str) -> dict:
    findings = []
    for line_no, line in enumerate(text.splitlines(), 1):
        paths = PATH.findall(line)
        hashes = HEX.findall(line)
        resolved = {p: resolve(p) for p in paths}
        for h in hashes:
            bound = [resolved[p] for p in paths if resolved[p] is not None]
            if not bound:
                continue  # unbound hash: not evidence for a file on this line
            ok = any(sha256(f).startswith(h) for f in bound)
            findings.append({
                "line": line_no, "kind": "HASH", "value": h[:16],
                "verdict": "PASS" if ok else "MISMATCH",
                "detail": "recomputed sha256 matches" if ok else "claimed hash does not match any file on this line",
            })
        for p, f in resolved.items():
            if f is None:
                findings.append({"line": line_no, "kind": "PATH", "value": p,
                                 "verdict": "MISSING", "detail": "referenced file does not exist"})
    for h in lint_contradictions(text):
        findings.append({"line": 0, "kind": "LINT", "value": h,
                         "verdict": "CONTRADICTION", "detail": h})

    bad = [f for f in findings if f["verdict"] not in ("PASS",)]
    return {
        "schema": "xoras.claim-verification.v1",
        "utc": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "verdict": "CLAIMS_PASS" if not bad else "CLAIMS_FAIL",
        "checks": len(findings),
        "failures": bad,
    }


def self_test() -> int:
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        f = d / "evidence.json"
        f.write_text('{"ok": true}\n')
        h = sha256(f)[:16]
        good = verify(f"Receipt `{f}` digest `{h}` is authoritative.", "selftest")
        bad = verify(f"Receipt `{f}` digest `deadbeefcafebabe` is authoritative.", "selftest")
        ok = good["verdict"] == "CLAIMS_PASS" and bad["verdict"] == "CLAIMS_FAIL"
        print(f"  {'PASS' if ok else 'FAIL'}  hash binding accepts truth / rejects fabrication")
        print("SELF TEST PASSED" if ok else "SELF TEST FAILED")
        return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Fail-closed claim verifier")
    ap.add_argument("report", nargs="?", help="report file to verify")
    ap.add_argument("--json", action="store_true", help="print JSON receipt")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.report:
        ap.error("report path required (or --self-test)")
    text = Path(args.report).read_text(encoding="utf-8")
    result = verify(text, str(Path(args.report).resolve()))
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"{result['verdict']}: {result['checks']} checks, {len(result['failures'])} failures")
        for f in result["failures"][:12]:
            print(f"  [{f['verdict']}] line {f['line']} {f['kind']} {f['value'][:70]}")
    return 0 if result["verdict"] == "CLAIMS_PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
