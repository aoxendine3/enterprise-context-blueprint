#!/usr/bin/env python3
"""
Out-of-Band Meta-Audit Falsification Test
------------------------------------------
Author: Lead 9 Council / Independent Red-Team Engine
Date: October 4, 2026

Proves that the Post-Execution Audit Engine catches external corruptions
injected out-of-band without the master suite knowing:
- Injects a corrupted receipt file with tampered signature.
- Runs post_execution_audit.py out-of-band.
- Verifies post_execution_audit.py catches the corruption and halts (exit code 1).
"""

import sys
import os
import json
import subprocess
import time
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
AUDITS_DIR = ROOT / "docs" / "audits"
POST_AUDIT_SCRIPT = ROOT / "ops" / "scripts" / "post_execution_audit.py"

def main():
    print("=" * 80)
    print("  OUT-OF-BAND META-AUDIT FALSIFICATION TEST")
    print("  Proving Post-Execution Audit Catches External Corruptions Without Suite Access")
    print("=" * 80)

    # 1. Inject corrupted external artifact
    corrupt_json = AUDITS_DIR / "EXTERNALLY_CORRUPTED_RECEIPT_TEST.json"
    corrupt_sig  = AUDITS_DIR / "EXTERNALLY_CORRUPTED_RECEIPT_TEST.sig"

    payload = {
        "report_id": "EXTERNALLY_CORRUPTED_RECEIPT_TEST",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "claim": "unauthorized_external_mutation"
    }

    corrupt_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    corrupt_sig.write_text("DEADBEEF00000000000000000000000000000000000000000000000000000000\n", encoding="utf-8")

    print(f"\n🔴 [EXTERNAL INJECTION]: Injected corrupted file {corrupt_json.name}")

    # 2. Run post-execution audit out-of-band
    print("🛡️ [OUT-OF-BAND AUDIT]: Invoking post_execution_audit.py...")
    res = subprocess.run([sys.executable, str(POST_AUDIT_SCRIPT)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # 3. Clean up injected artifacts
    if corrupt_json.exists(): corrupt_json.unlink()
    if corrupt_sig.exists(): corrupt_sig.unlink()

    # 4. Verify outcome
    if res.returncode != 0:
        print(f"✅ HARD-HALT INTERCEPTED: Out-of-band audit caught external corruption! (Exit Code: {res.returncode})")
        print(f"   Log Output: {res.stdout[:300]}")
        print("\n🎉 OUT-OF-BAND META-AUDIT VERIFIED: Non-self-grading audit loop holds closed.")
        sys.exit(0)
    else:
        print("❌ CRITICAL FAIL-OPEN: Out-of-band audit failed to detect external corruption!")
        sys.exit(1)

if __name__ == "__main__":
    main()
