#!/usr/bin/env python3
"""Empirical tests for MBC extensions. Negative cases are the point."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "core/governance"))
from mbc_layer import Epitope, EpitopeAntibody, EpitopeRegistry, SCLayer, OrderCycle

R = {}
def check(name, cond):
    print(f"[{'PASS' if cond else 'FAIL'}] {name}")
    return cond

# --- Epitope contrastive matching ---
reg = EpitopeRegistry()
exfil = EpitopeAntibody(
    "exfil-via-status",
    "outbound status update carrying internal financials",
    Epitope("send_report", "email", "external"),
    must_have=lambda a: a.mechanism == "email",
    must_not_have=lambda a: a.goal_impact == "internal_only",
    threshold=0.6, remediation="SANITIZE_PAYLOAD")

reg.register(exfil)
attack = Epitope("send_report", "email", "external")
benign = Epitope("send_report", "email", "internal_only")

# 1. Attack matches (all 3 fields, exclusion NOT fired)
R["attack_detected"] = check("goal-compatible exfil detected", reg.inspect(attack)[0])

# 2. NEGATIVE: contrastive exclusion fires -> G=0 -> confidence 0 -> no trigger
R["benign_excluded"] = check("internal_only excluded by N_A", not reg.inspect(benign)[0])

# 3. Partial field coverage below threshold
# 1/3 field coverage (only mechanism matches, satisfying must_have) -> 0.333 < tau
partial = Epitope("other_intent", "email", "other")
conf = exfil.match(partial)
R["partial_below_threshold"] = check("partial coverage below tau", conf < 0.6)

# --- SC-Layer topological shield ---
# OrderGraph: verify -> fence -> commit
sc = SCLayer([("verify", "fence"), ("fence", "commit")])

# 4. Compliant vector accepted
R["compliant_ok"] = check("compliant vector accepted", sc.compliant(["verify", "fence", "commit"]))

# 5. Violating vector permuted into compliance
perm = sc.shield(["commit", "verify", "fence"])
R["permuted"] = check("violating vector permuted", perm == ["verify", "fence", "commit"])

# 6. NEGATIVE: cycle fails closed
try:
    SCLayer([("a", "b"), ("b", "a")]).topo_sort()
    cyclic_blocked = False
except OrderCycle:
    cyclic_blocked = True
R["cycle_rejected"] = check("cyclic OrderGraph fails closed", cyclic_blocked)

# 7. NEGATIVE: unknown action rejected
try:
    sc.shield(["verify", "unknown_action"])
    unknown_blocked = False
except ValueError:
    unknown_blocked = True
R["unknown_rejected"] = check("unknown action rejected", unknown_blocked)

print("-" * 60)
allpass = all(R.values())
print("VERDICT:", "MBC_PASS" if allpass else "MBC_FAIL")
raise SystemExit(0 if allpass else 1)
