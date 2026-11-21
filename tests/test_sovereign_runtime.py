#!/usr/bin/env python3
"""Empirical tests for the no-wheel Sovereign Runtime. Formal proof NOT attached."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "core/governance"))
from sovereign_runtime import (SovereignRuntime, PlanFence, Proposal, Capability,
                               SealedCapability)

rt = SovereignRuntime()
obj = rt.seed("app.config", "endpoint", {"url": "https://a.internal", "port": 443})
cap = rt.ledger.issue("reasoner-1", "app.config", "write", rank=5, expires_epoch=10)


def prop(fence=None, cap_override=None, payload=None, verb="write"):
    return Proposal("reasoner-1", cap_override or cap,
                    fence or PlanFence.for_object(obj), verb,
                    payload or {"url": "https://b.internal", "port": 443})


def check(name, cond):
    print(f"[{'PASS' if cond else 'FAIL'}] {name}")
    return cond

R = {}
# 1. Valid two-phase commit
p = prop()
ok1, _ = rt.prepare(p); ok2, rid = rt.commit(p)
R["valid_two_phase_commit"] = check("valid two-phase commit -> receipt", ok1 and ok2 and len(rid) == 64)

# 2. NEGATIVE: forged capability
forged = SealedCapability(cap.cap, "0" * 64)
ok, why = rt.prepare(prop(cap_override=forged))
R["forged_capability_rejected"] = check("forged capability -> rejected", not ok and why == "CAPABILITY_FORGED")

# 3. NEGATIVE: scope escape — legit object exists, but capability is for a different scope
rt.seed("system.secrets", "x", {"token": "v"})   # target object exists
esc = rt.ledger.issue("reasoner-1", "system.secrets", "write", rank=5, expires_epoch=10)
bad_fence = PlanFence("system.secrets", "x", rt.objects[("system.secrets", "x")].digest(), 1)
# Use a capability issued for app.config against system.secrets:
ok, why = rt.prepare(prop(cap_override=cap, fence=bad_fence))
R["scope_escape_rejected"] = check("scope escape -> rejected", not ok and why == "SCOPE_ESCAPE")

# 4. NEGATIVE: stale plan (fresh memory, stale plan paradox)
stale = PlanFence("app.config", "endpoint", obj.digest(), obj.version - 1)
ok, why = rt.prepare(prop(fence=stale))
R["stale_plan_rejected"] = check("stale plan -> rejected", not ok and why == "GATE1_PLAN_STALE")

# 5. NEGATIVE: revoked capability
rt.ledger.revoke(cap.cap.nonce)
ok, why = rt.prepare(prop())
R["revoked_capability_rejected"] = check("revoked capability -> rejected", not ok and why == "CAPABILITY_REVOKED")

# 6. NEGATIVE: no real state mutation on failed prepare (no dirty writes)
after = rt.objects[("app.config", "endpoint")]
R["no_dirty_write"] = check("failed writes left real state unchanged",
                            after.payload == {"url": "https://b.internal", "port": 443})

# 7. Immune ledger recorded antigens from failures
h = rt.health()
R["antigen_ledger_populated"] = check("failures raised immune antigens", h["antigens"] >= 4)

# 8. Rank supremacy antibody: low-rank write blocked (need a fresh non-revoked, fresh-fence proposal)
cap2 = rt.ledger.issue("r", "app.config", "write", rank=0, expires_epoch=10)
fresh = PlanFence.for_object(rt.objects[("app.config", "endpoint")])
p2 = Proposal("r", cap2, fresh, "write", {"url": "x"})
ok, why = rt.prepare(p2)
R["rank_supremacy_enforced"] = check("rank-0 write blocked by antibody", not ok and "NEUTRALIZED" in why)

print("-" * 60)
allpass = all(R.values())
print("VERDICT:", "RUNTIME_PASS" if allpass else "RUNTIME_FAIL")
raise SystemExit(0 if allpass else 1)
