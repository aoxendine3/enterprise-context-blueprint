#!/usr/bin/env python3
"""
Differential check: Lean 4 kernel verdicts vs Z3 verdicts on the same statements.

Mapping (each row is one statement checked by two independent tools):
  Lean `step_monotone`              proved   <->  Z3 agm_mtpo_monotonicity.smt2          unsat
  Lean `destructive_not_monotone`   proved   <->  Z3 agm_unconstrained_violation.smt2    sat
  Lean `mutant_not_monotone`        proved   <->  Z3 mutated MTPO file                   sat

Also checks:
  * no `sorryAx` and no unexpected axioms in any headline theorem
  * Lean REJECTS a deliberately false claim (Lean-side non-vacuity)
Exit code is non-zero on any disagreement or failed check.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEAN = HERE / "lean"
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
FAILS = []

def expect(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name} {detail}")
    if not cond:
        FAILS.append(name)

def sh(cmd, cwd=None):
    env = dict(os.environ)
    elan_bin = Path.home() / ".elan/bin"
    if elan_bin.exists():
        env["PATH"] = str(elan_bin) + os.pathsep + env["PATH"]
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)

def z3_status(path):
    out = sh(["z3", str(path)]).stdout.split()
    return out[0] if out else "error"

def main():
    elan_bin = Path.home() / ".elan/bin"
    has_lake = shutil.which("lake") or (elan_bin / "lake").exists()
    if not has_lake:
        print("lake not found; install elan (https://github.com/leanprover/elan)")
        sys.exit(2)

    print("[1/4] lake build (kernel checks every proof term)")
    b = sh(["lake", "build"], cwd=LEAN)
    text = b.stdout + b.stderr
    expect("lake build exits 0", b.returncode == 0)
    if b.returncode != 0:
        print(text[-2000:])

    print("[2/4] axiom audit")
    axioms = {}
    for m in re.finditer(r"'Mtpo\.(\w+)' (depends on axioms: \[(.*?)\]|does not depend on any axioms)", text, re.S):
        axioms[m.group(1)] = set() if m.group(3) is None else {a.strip() for a in m.group(3).split(",")}
    headline = ["step_monotone", "reaches_monotone", "destructive_not_monotone", "mutant_not_monotone"]
    for t in headline:
        expect(f"{t}: axioms reported", t in axioms)
        if t in axioms:
            expect(f"{t}: no sorryAx / unexpected axioms", axioms[t] <= ALLOWED_AXIOMS, str(sorted(axioms[t])))
    expect("no 'sorry' warning in build output", "sorry" not in text.lower())

    print("[3/4] Lean vs Z3 differential")
    mtpo = HERE / "agm_mtpo_monotonicity.smt2"
    mut_src = mtpo.read_text().replace("(store H n (- (select H k)))", "(store H k (- (select H k)))")
    with tempfile.NamedTemporaryFile("w", suffix=".smt2", delete=False) as f:
        f.write(mut_src)
    rows = [
        ("step_monotone", z3_status(mtpo), "unsat"),
        ("destructive_not_monotone", z3_status(HERE / "agm_unconstrained_violation.smt2"), "sat"),
        ("mutant_not_monotone", z3_status(f.name), "sat"),
    ]
    os.unlink(f.name)
    for thm, z3v, want in rows:
        lean_ok = thm in axioms and b.returncode == 0
        agree = lean_ok and z3v == want
        expect(f"{thm}: Lean proved & Z3={z3v} (expected {want})", agree)

    print("[4/4] Lean rejects a false claim (non-vacuity)")
    bad = LEAN / "_FalseClaim.lean"
    bad.write_text(
        "import MtpoMonotonicity.Basic\nopen Mtpo\n"
        "-- FALSE: claims the overwrite mutant is monotone for all inputs\n"
        "theorem bogus (H : Int → Int) (n k : Int) (hk : 0 ≤ k) (hk2 : k < n) :\n"
        "    Monotone H n (sagaMutant H n k).1 (sagaMutant H n k).2 := by\n"
        "  refine ⟨by simp [sagaMutant]; omega, ?_⟩\n"
        "  intro i _ hi\n  simp [sagaMutant, store]\n  omega\n")
    r = sh(["lake", "env", "lean", str(bad)], cwd=LEAN)
    if bad.exists():
        bad.unlink()
    expect("false theorem is rejected by the kernel/elaborator", r.returncode != 0)

    verdict = "PASS" if not FAILS else "FAIL"
    receipt = {
        "verdict": verdict,
        "failures": FAILS,
        "axioms": {k: sorted(v) for k, v in axioms.items()},
        "z3_rows": [{"theorem": t, "z3": z, "expected": w} for t, z, w in rows],
        "toolchain": (LEAN / "lean-toolchain").read_text().strip()
    }
    receipt_path = Path.cwd() / "lean_differential_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2))
    print(f"\nVERDICT: {verdict} | Receipt written to {receipt_path}")
    sys.exit(0 if not FAILS else 1)

if __name__ == "__main__":
    main()
