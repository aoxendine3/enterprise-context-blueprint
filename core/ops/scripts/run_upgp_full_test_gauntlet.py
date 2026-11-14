#!/usr/bin/env python3
"""
UPGP Full Proving Ground Runner
===============================
Runs only what actually exists in this repository, exits non-zero on any failure:

1. Z3 SMT-LIB v2 formal proofs (upgp_containment_proof, mtpo_preorder_invariant)
   — requires the `z3` binary or the `z3-solver` Python package.
2. Red-Team C Exploit Harness (tests/RedTeamExploitGauntlet.ts, 5 baseline vectors)
   — requires node >= 22.6 for --experimental-strip-types.

Removed (with receipt, barn/archives/theatrical_fake_pass/):
   - hard-coded REPO_ROOT pointing at a developer machine
   - theatrical "15-Vector TS Escape Gauntlet" whose PASS lines were printed, unmeasured
   - council speech dispatch narrated as "proof"
   - the fallthrough that exited 0 even when checks failed
"""
import os
import subprocess
import sys
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LOG_PATH = os.path.join(REPO_ROOT, "memory", "catch_log", "upgp_full_test_suite.log")

PROOF_FILES = [
    "core/ops/security/upgp_containment_proof.smt2",
    "core/ops/security/mtpo_preorder_invariant.smt2",
]

def run(cmd, **kw):
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, **kw)

def check_z3(log):
    z3_bin = None
    for cand in ("/opt/homebrew/bin/z3", "/usr/local/bin/z3", "z3"):
        for exe in (cand if os.path.isabs(cand) else [os.path.join(p, cand) for p in os.environ.get("PATH", "").split(os.pathsep)]):
            if os.path.isfile(exe) and os.access(exe, os.X_OK):
                z3_bin = exe
                break
        if z3_bin:
            break
    if not z3_bin:
        print("[FAIL] z3 binary not found — install z3 or `pip install z3-solver`")
        log.write("Z3: MISSING BINARY\n")
        return False
    ok = True
    for rel in PROOF_FILES:
        path = os.path.join(REPO_ROOT, rel)
        if not os.path.isfile(path):
            print(f"[FAIL] missing proof file: {rel}")
            log.write(f"Z3 {rel}: MISSING\n")
            ok = False
            continue
        res = run([z3_bin, "-smt2", "-T:30", path], timeout=45)
        verdict = res.stdout.strip().splitlines()[0] if res.stdout.strip() else "NO OUTPUT"
        print(f"[z3] {rel}: {verdict}")
        log.write(f"Z3 {rel}: {verdict}\n")
        if "unsat" not in res.stdout.lower():
            ok = False
    return ok

def check_red_team(log):
    res = run(["node", "--experimental-strip-types", "tests/RedTeamExploitGauntlet.ts"], timeout=180)
    tail = (res.stdout or "").strip().splitlines()[-3:]
    for line in tail:
        print(line)
    log.write("RED TEAM TAIL:\n" + (res.stdout or "")[-2000:] + "\n")
    return res.returncode == 0

def main():
    time.strftime("%Y-%m-%dT%H:%M:%S%z")
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    failures = []
    with open(LOG_PATH, "a", encoding="utf-8") as log:
        log.write(f"==== upgp_full_test_suite {time.strftime('%Y-%m-%d %H:%M:%S')} ====\n")
        print("== [1/2] Z3 SMT formal proofs ==")
        if not check_z3(log):
            failures.append("z3")
        print("== [2/2] Red-team C exploit harness ==")
        if not check_red_team(log):
            failures.append("red-team")
        log.write(f"FAILURES: {failures or 'none'}\n")
    if failures:
        print(f"\n[FAIL] proving ground FAILED: {', '.join(failures)}", file=sys.stderr)
        sys.exit(1)
    print("\n[PASS] proving ground: all executed checks discharged.")

if __name__ == "__main__":
    main()
