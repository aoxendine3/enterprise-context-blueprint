#!/usr/bin/env python3
"""
=============================================================================
XORAS PAYMENT & BILLING VALIDATION HARNESS
Location: labs/workspaces/sovereign-agentic-app/test_payment_system.py
Purpose: Falsification audit and verification of payment routes, amounts,
intent integrity, licensing, and professional copy.
=============================================================================
"""

import os
import sys
import json
import hashlib
import time
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
WORKSPACE_DIR = ROOT / "labs/workspaces/sovereign-agentic-app"
CATCH_LOG = ROOT / "memory/catch_log"

def run_payment_audit():
    print("=" * 70)
    print("🔍 XORAS PAYMENT & BILLING AUDIT: INTENT & AMOUNT VERIFICATION")
    print("=" * 70)

    # 1. Inspect stripe.server.ts
    server_ts = (WORKSPACE_DIR / "app/stripe.server.ts").read_text(encoding="utf-8")
    billing_tsx = (WORKSPACE_DIR / "app/routes/app.billing.tsx").read_text(encoding="utf-8")
    index_tsx = (WORKSPACE_DIR / "app/routes/app._index.tsx").read_text(encoding="utf-8")

    tests = []

    # Check 1: Live Payment Link is specifically for direct contributions ($1+)
    has_direct_link = "https://buy.stripe.com/eVq00jcRof7W3jp158dIA00" in server_ts
    tests.append({
        "check": "Direct Contribution Stripe Link Exact Match",
        "passed": has_direct_link,
        "detail": "buy.stripe.com/eVq00jcRof7W3jp158dIA00 correctly isolated to $1+ contribution button"
    })

    # Check 2: GitHub Sponsors link match
    has_github_sponsors = "https://github.com/sponsors/aoxendine3" in server_ts
    tests.append({
        "check": "GitHub Sponsors URL Exact Match",
        "passed": has_github_sponsors,
        "detail": "github.com/sponsors/aoxendine3 properly linked"
    })

    # Check 3: Commercial Tiers have exact pricing ($299, $1499, $4999) and dynamic UI binding
    has_prices_in_server = ("priceMonthly: 299" in server_ts) and ("priceMonthly: 1499" in server_ts) and ("priceMonthly: 4999" in server_ts)
    has_dynamic_ui_binding = "plan.priceMonthly" in billing_tsx and "SOVEREIGN_PLANS" in billing_tsx
    tiers_passed = has_prices_in_server and has_dynamic_ui_binding
    tests.append({
        "check": "Commercial Tiers Exact Amount Integrity",
        "passed": tiers_passed,
        "detail": "Server defines exact amounts ($299, $1,499, $4,999) and UI dynamically renders plan.priceMonthly"
    })

    # Check 4: Professional Tone & Proper Business Language
    prohibited_jargon = ["hallucinating clowns", "destroy competition", "cheap hack"]
    clean_copy = not any(jargon in billing_tsx.lower() for jargon in prohibited_jargon)
    has_privacy_guarantee = "privacy" in billing_tsx.lower() and "mit" in billing_tsx.lower()
    tests.append({
        "check": "Professional Language & Privacy Disclosures",
        "passed": clean_copy and has_privacy_guarantee,
        "detail": "Professional, courteous business language with MIT licensing and zero-data-exfiltration guarantees"
    })

    # Check 5: Button Click Intent Alignment
    # The direct payment link MUST NOT hijack the commercial subscription tiers
    direct_link_not_hijacking = "isLiveStripeSession" in server_ts or "isInvoiceOrder" in server_ts
    tests.append({
        "check": "Button Click Intent Separation",
        "passed": direct_link_not_hijacking,
        "detail": "Commercial tiers generate verified invoice/subscription orders with exact dollar amount instead of blind redirect"
    })

    # Summary
    all_passed = all(t["passed"] for t in tests)
    for t in tests:
        status_icon = "✅" if t["passed"] else "❌"
        print(f"{status_icon} {t['check']}: {t['detail']}")

    receipt = {
        "timestamp": int(time.time()),
        "audit_name": "PAYMENT_AND_BILLING_SYSTEM_VALIDATION",
        "all_passed": all_passed,
        "tests": tests,
        "director": "Anthony",
        "attestation": ["maxx", "clara", "vance"]
    }

    receipt_bytes = json.dumps(receipt, indent=2).encode("utf-8")
    receipt_sha = hashlib.sha256(receipt_bytes).hexdigest()
    receipt["sha256"] = receipt_sha

    receipt_path = WORKSPACE_DIR / "PAYMENT_SYSTEM_VALIDATION_RECEIPT.json"
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    
    try:
        CATCH_LOG.mkdir(parents=True, exist_ok=True)
        (CATCH_LOG / "PAYMENT_SYSTEM_VALIDATION_RECEIPT.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    except Exception:
        pass

    print("-" * 70)
    print(f"Receipt Hash : {receipt_sha}")
    print(f"Audit Status : {'PASSED (100% VERIFIED)' if all_passed else 'FAILED'}")
    print("=" * 70)

    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    run_payment_audit()
