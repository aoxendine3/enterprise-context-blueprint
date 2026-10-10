#!/usr/bin/env python3
"""
XORAS::OS - AGENTS.md Compliance & Context Engine
Zero-dependency CLI tool to audit repository agentic contracts.
"""

import os
import sys

def audit_agents_md(filepath="AGENTS.md"):
    print("\n🛡️  XORAS::OS AGENTS.md Compliance Audit 🛡️\n" + "="*45)
    
    if not os.path.exists(filepath):
        print(f"❌ CRITICAL FAIL: '{filepath}' not found.")
        print("Your agents are running blind without a governance contract.")
        sys.exit(1)

    with open(filepath, "r") as f:
        content = f.read().lower()

    score = 0
    checks = {
        "Identity & Invariants (Fail-Closed)": ["fail closed", "invariant"],
        "Trinity Gate (2-of-3 Consensus)": ["trinity gate"],
        "Sacred /core/ vs /barn/ Boundary": ["/barn/"],
        "Immutable State (chflags lock)": ["chflags"],
        "Self-Healing & Remediation": ["self-healing", "remediate"]
    }

    for name, keywords in checks.items():
        if any(kw in content for kw in keywords):
            print(f"✅ PASS: {name}")
            score += 20
        else:
            print(f"❌ FAIL: Missing {name}")

    print("="*45)
    print(f"Final Compliance Score: {score}%")
    
    if score == 100:
        print("🚀 STATUS: Enterprise Swarm Ready. Welcome to the Sovereign Citadel.")
    elif score >= 60:
        print("⚠️ STATUS: Partial Compliance. Vulnerable to context drift.")
        print("   -> Upgrade to XORAS SaaS ($49/mo) for continuous drift monitoring.")
    else:
        print("🚨 STATUS: High Risk. Multi-agent state collisions imminent.")
        print("   -> Run 'xoras-audit --generate' to scaffold a secure AGENTS.md.")
    print("\n")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "AGENTS.md"
    audit_agents_md(target)
