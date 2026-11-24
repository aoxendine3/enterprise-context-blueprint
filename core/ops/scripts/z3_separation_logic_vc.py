#!/usr/bin/env python3
"""
Z3 SEPARATION-LOGIC VERIFICATION CONDITIONS — two-cell pointer swap.

The XORAS Bio-Cognitive Core video (chapter 2) claims: "Separation Logic
proves the absence of pointer and data races" (aliasing crossed out). This
script makes that claim checkable for the canonical example: swapping the
contents of two heap cells through pointers while a third cell is framed.

Program (Hoare triple with separating conjunction):

    pre:  a ↦ x  *  b ↦ y  *  f ↦ z          (a, b, f pairwise distinct)
          tmp := [a];
          [a] := [b];
          [b] := tmp;
    post: a ↦ y  *  b ↦ x  *  f ↦ z

Encoding note (honest): the heap is a Z3 Array(Int -> Int); points-to
p ↦ v is Select(H,p) == v; separating conjunction for concrete addresses
adds pairwise disequality (disjointness). This proves, in QF array theory:

  VC1_swap_post      : the swap establishes a↦y * b↦x under a≠b.
  VC2_frame_rule     : the frame instance — any cell f disjoint from a,b
                       keeps its value (no interference = no race).

NEGATIVE CONTROLS (the check must have teeth):
  CTRL1_aliased_frame: drop f≠a ∧ f≠b — frame preservation must be REFUTED
                       (SAT counterexample where the write clobbers the frame).
  CTRL2_tampered_post: claim the swap leaves a↦x — must be REFUTED (SAT).

Scope boundary (honest): this is a real machine-checked proof of the frame-
rule instance for one concrete program over SMT array theory — not a proof
of a full separation-logic metalanguage. UNKNOWN is never accepted as
"refuted": controls require SAT with an explicit model.

Fail closed: any VC invalid or control not refuted => non-zero exit.
Writes memory/catch_log/Z3_SEPARATION_LOGIC_RECEIPT.json.
"""
import sys
import time
import json
from pathlib import Path
from z3 import *

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
RECEIPT = ROOT / "memory/catch_log/Z3_SEPARATION_LOGIC_RECEIPT.json"

# Heap and program variables.
H = Array("H", IntSort(), IntSort())
a, b, f = Ints("a b f")
x, y, z = Ints("x y z")

# Straight-line execution: tmp := [a]; [a] := [b]; [b] := tmp
tmp = Select(H, a)
H1 = Store(H, a, Select(H, b))   # [a] := [b]
H2 = Store(H1, b, tmp)           # [b] := tmp

# Separating conjunction of concrete points-to facts (with disjointness).
pre_swap = And(Select(H, a) == x, Select(H, b) == y, a != b)
pre_frame = And(pre_swap, Select(H, f) == z, f != a, f != b)


def prove(name, formula):
    """Validity = negation UNSAT. Returns (valid, seconds, detail, raw_result).

    raw_result is separate so callers can require a SPECIFIC outcome —
    negative controls need SAT with a model; UNKNOWN is not refutation.
    """
    s = Solver()
    s.add(Not(formula))
    t0 = time.time()
    r = s.check()
    dt = round(time.time() - t0, 4)
    if r == unsat:
        return True, dt, "UNSAT (valid)", r
    if r == sat:
        return False, dt, "SAT — counterexample: " + str(s.model())[:300], r
    return False, dt, f"UNKNOWN: {s.reason_unknown()}", r


def refute(name, formula):
    """Negative control: the formula must be INVALID, proven by a concrete
    counterexample (SAT + model). UNKNOWN/UNSAT => control failed."""
    s = Solver()
    s.add(Not(formula))
    t0 = time.time()
    r = s.check()
    dt = round(time.time() - t0, 4)
    blocked = (r == sat)
    if blocked:
        detail = "SAT — counterexample: " + str(s.model())[:300]
    elif r == unknown:
        detail = f"UNKNOWN: {s.reason_unknown()} (not accepted as refuted)"
    else:
        detail = "UNSAT — false claim was NOT refuted (checker has no teeth)"
    return blocked, dt, detail, r


def main():
    results = {}

    # VC1: pre_swap → a↦y ∧ b↦x after the swap.
    vc1_post = And(Select(H2, a) == y, Select(H2, b) == x)
    results["VC1_swap_post"] = prove("VC1", Implies(pre_swap, vc1_post))

    # VC2: frame instance — disjoint f keeps its value (no interference).
    vc2_frame = Select(H2, f) == Select(H, f)
    results["VC2_frame_rule"] = prove("VC2", Implies(pre_frame, vc2_frame))

    # NEGATIVE CONTROL 1: same frame claim with f allowed to alias a or b.
    # The write to [a] (or [b]) must clobber the frame — counterexample.
    ctrl1_pre = And(Select(H, a) == x, Select(H, b) == y,
                    Select(H, f) == z, a != b)          # NO f≠a, f≠b
    c1_ok, c1_dt, c1_detail, c1_raw = refute(
        "CTRL1", Implies(ctrl1_pre, Select(H2, f) == Select(H, f)))

    # NEGATIVE CONTROL 2: tampered post — swap claimed to leave a↦x.
    c2_ok, c2_dt, c2_detail, c2_raw = refute(
        "CTRL2", Implies(pre_swap, Select(H2, a) == x))

    all_valid = all(results[k][0] for k in results)
    verdict = "Z3_SEPARATION_VC_PASS" if (all_valid and c1_ok and c2_ok) \
        else "Z3_SEPARATION_VC_FAIL"

    payload = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "verdict": verdict,
        "z3_version": get_version_string(),
        "encoding": "heap = Array(Int,Int); p↦v = Select(H,p)==v; "
                    "* = pairwise disequality (concrete disjointness); "
                    "swap = two Stores over circular program order",
        "vcs": {k: {"valid": v[0], "seconds": v[1], "detail": v[2]}
                for k, v in results.items()},
        "negative_controls": {
            "CTRL1_aliased_frame": {"refuted": c1_ok, "seconds": c1_dt,
                                    "detail": c1_detail},
            "CTRL2_tampered_post": {"refuted": c2_ok, "seconds": c2_dt,
                                    "detail": c2_detail},
        },
        "scope": "frame-rule instance for a concrete two-cell swap over SMT "
                 "array theory; not a full separation-logic metalanguage",
    }
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(payload, indent=2))

    print(f"Z3 {get_version_string()} — separation-logic frame-rule VCs")
    print("-" * 66)
    for k, (ok, dt, detail, _raw) in results.items():
        print(f"[{'PASS' if ok else 'FAIL'}] {k:22} {dt:>7}s  {detail[:66]}")
    print(f"[{'PASS' if c1_ok else 'FAIL'}] {'CTRL1_aliased_frame':22} "
          f"{c1_dt:>7}s  refuted={c1_ok}")
    print(f"[{'PASS' if c2_ok else 'FAIL'}] {'CTRL2_tampered_post':22} "
          f"{c2_dt:>7}s  refuted={c2_ok}")
    print("-" * 66)
    print("VERDICT:", verdict, "| receipt:", RECEIPT)
    return 0 if verdict == "Z3_SEPARATION_VC_PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
