#!/usr/bin/env python3
"""
Z3 VERIFICATION-CONDITION PROOF — integer exponentiation loop.
Proves VC1 (init), VC2 (preservation), VC3 (post) from the 'memory-and-proofs'
synthesis, for the program:

    pre:  x = x0 ∧ n = n0 ∧ n0 ≥ 0
    y := 1; i := n;
    while i > 0:  y := y*x;  i := i-1
    post: y = x0^n0
    invariant I ≡ (y · x^i = x0^n0) ∧ i ≥ 0

Encoding note (honest): Z3 has no native symbolic-exponent arithmetic over Int.
We axiomatize pow as a total Int×Int→Int function with its two defining
equations (pow(x,0)=1; i>0 → pow(x,i)=x·pow(x,i-1)) and prove the VCs over
universally quantified integers under those axioms. This is a real universal
proof relative to the defining equations — NOT a bounded test, NOT a claim
about Z3's built-in `**`.

Fail closed: any VC invalid => non-zero exit. Negative control must be refuted.
Writes memory/catch_log/Z3_EXPONENTIATION_VC_RECEIPT.json.
"""
import sys, time, json
from pathlib import Path
from z3 import *

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
RECEIPT = ROOT / "memory/catch_log/Z3_EXPONENTIATION_VC_RECEIPT.json"

x, x0, n, n0, y, i = Ints("x x0 n n0 y i")
powf = Function("pow", IntSort(), IntSort(), IntSort())

# Defining equations of exponentiation for non-negative exponents.
ax_base = ForAll([x], powf(x, 0) == 1)
ax_step = ForAll([x, i], Implies(i > 0, powf(x, i) == x * powf(x, i - 1)))
AXIOMS = [ax_base, ax_step]

I = And(y * powf(x, i) == powf(x0, n0), i >= 0)  # invariant


def wp_seq(assignments, body):
    """Weakest precondition by reverse substitution for straight-line assigns."""
    out = body
    for var, expr in reversed(assignments):
        out = simplify(substitute(out, (var, expr)))
    return out


def prove(name, formula):
    """Validity = negation UNSAT. Returns (valid, seconds, detail)."""
    s = Solver()
    s.add(*AXIOMS)
    s.add(Not(formula))
    t0 = time.time()
    r = s.check()
    dt = round(time.time() - t0, 4)
    if r == unsat:
        return True, dt, "UNSAT (formula valid under pow axioms)"
    if r == sat:
        return False, dt, "SAT — counterexample: " + str(s.model())[:300]
    return False, dt, f"UNKNOWN: {s.reason_unknown()}"


def main():
    results = {}

    # VC1: (x=x0 ∧ n=n0 ∧ n0≥0) → wp(y:=1; i:=n, I)
    vc1_pre = And(x == x0, n == n0, n0 >= 0)
    vc1_post = substitute(I, (y, IntVal(1)), (i, n))  # y:=1 then i:=n
    results["VC1_init"] = prove("VC1", Implies(vc1_pre, vc1_post))

    # VC2: (I ∧ i>0) → wp(y:=y*x; i:=i-1, I)
    guard = And(I, i > 0)
    # Sequential y:=y*x; i:=i-1 -> reverse substitution: i-1 first, then y*x
    vc2_post = substitute(I, (i, i - 1))
    vc2_post = substitute(vc2_post, (y, y * x))
    results["VC2_preservation"] = prove("VC2", Implies(guard, vc2_post))

    # VC3: (I ∧ ¬(i>0)) → (y = pow(x0,n0))  [postcondition y = x0^n0]
    vc3_pre = And(I, Not(i > 0))
    results["VC3_post"] = prove("VC3", Implies(vc3_pre, y == powf(x0, n0)))

    # NEGATIVE CONTROL: a FALSE postcondition (y = x0^n0 + 1) must be refuted.
    # Under I ∧ ¬(i>0) we get i=0 and y·x^0 = y = pow(x0,n0), so y = pow+1
    # is unsatisfiable — Z3 must find a counterexample, proving the check has teeth.
    bad_claim = Implies(vc3_pre, y == powf(x0, n0) + 1)
    bad_valid, bad_dt, bad_detail = prove("VC3_false_post", bad_claim)
    control_blocked = not bad_valid

    all_valid = all(results[k][0] for k in ("VC1_init", "VC2_preservation", "VC3_post"))
    verdict = "Z3_VC_PROOF_PASS" if (all_valid and control_blocked) else "Z3_VC_PROOF_FAIL"

    payload = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "verdict": verdict,
        "z3_version": get_version_string(),
        "encoding": "pow axiomatized by pow(x,0)=1 and i>0→pow(x,i)=x·pow(x,i-1); universal Int quantifiers",
        "vcs": {k: {"valid": v[0], "seconds": v[1], "detail": v[2]} for k, v in results.items()},
        "negative_control": {"tampered_invariant_refuted": control_blocked,
                             "seconds": bad_dt, "detail": bad_detail},
    }
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(payload, indent=2))

    print(f"Z3 {get_version_string()} — exponentiation VC proof")
    print("-" * 66)
    for k, (ok, dt, detail) in results.items():
        print(f"[{'PASS' if ok else 'FAIL'}] {k:20} {dt:>7}s  {detail[:70]}")
    print(f"[{'PASS' if control_blocked else 'FAIL'}] {'NEGATIVE_CONTROL':20} {bad_dt:>7}s  tampered invariant refuted={control_blocked}")
    print("-" * 66)
    print("VERDICT:", verdict, "| receipt:", RECEIPT)
    return 0 if verdict == "Z3_VC_PROOF_PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
