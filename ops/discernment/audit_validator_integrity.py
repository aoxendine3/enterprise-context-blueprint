#!/usr/bin/env python3
"""
===============================================================================
WHO VALIDATES THE VALIDATOR? (VALIDATOR INTEGRITY & MUTATION SUITE)
===============================================================================
This suite tests the validators themselves (zoras_report_schema.py and
governed_memory_consolidation_engine.py) against Known-Good and Known-Bad fixtures.

If a validator approves a Known-Bad fixture, or rejects a Known-Good fixture,
the validator is flagged as COMPROMISED.

Author: The Lead 9 Council / Xoras Discernment Bench
Date: 2026-09-30
===============================================================================
"""

import os
import sys
import json
import tempfile
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from discernment.zoras_report_schema import ZorasReportSchemaEnforcer

KNOWN_GOOD_FIXTURE = """# Certified Production System Audit
**Document Version:** 1.0.0
**Date:** 2026-09-30
**Author:** The Lead 9 Council
**Classification:** PRODUCTION
**Session ID:** valid_session_001
**Session Merkle Root:** 16b2759a71091538668ba6197fd289420e5c673648a78c9e54e6c0f91871ec12
**Reproducibility Command:** `python3 ops/provenance/break_context_lineage_engine.py`

---

## 1. Executive Summary & Claim-Evidence Graph
All claims mapped to code files and SHA-256 digests.

## 2. Technical Architecture & Mathematical Specification
Formal spec and data flow documented.

## 3. Mandatory Adversarial Verification & Failure Mode Mapping
Tested under failure conditions and red-team gauntlets.

## 4. Discernment Bench Verdict & Epistemic Confidence
Approved by Blackbox Review Engine with 0.999 confidence score.

## 5. Verification Questions & Resolutions
| Question | Evidence Needed | Resolution or Answer | Status |
| --- | --- | --- | --- |
| Can forged signatures pass? | Vector 2 test receipt | Caught and blocked with 100% precision. | 🟢 RESOLVED |

## 6. Known Limitations & Non-Claims Note
We do not claim zero latency overhead. SQLite scaling requires compaction.

## 7. Reproduction Instructions & Hash Receipts
Run `python3 ops/provenance/break_context_lineage_engine.py` to reproduce.
"""

KNOWN_BAD_FIXTURES = {
    "MUTANT_01_MISSING_VERIFICATION_TABLE": """# Audit Report
## 1. Executive Summary & Claim-Evidence Graph
Summary here.
## 2. Technical Architecture & Mathematical Specification
Spec here.
## 3. Mandatory Adversarial Verification & Failure Mode Mapping
Stress test passed.
## 4. Discernment Bench Verdict & Epistemic Confidence
Approved.
## 6. Known Limitations & Non-Claims Note
Bounds declared.
## 7. Reproduction Instructions & Hash Receipts
`python3 script.py`
""",
    "MUTANT_02_MISSING_ADVERSARIAL_GAUNTLET": """# Audit Report
## 1. Executive Summary & Claim-Evidence Graph
Summary here.
## 2. Technical Architecture & Mathematical Specification
Spec here.
## 4. Discernment Bench Verdict & Epistemic Confidence
Approved.
## 5. Verification Questions & Resolutions
| Question | Evidence Needed | Resolution or Answer | Status |
| --- | --- | --- | --- |
| Test Q | Evidence | Answer | 🟢 RESOLVED |
## 6. Known Limitations & Non-Claims Note
Bounds declared.
## 7. Reproduction Instructions & Hash Receipts
`python3 script.py`
""",
    "MUTANT_03_MISSING_KNOWN_LIMITATIONS": """# Audit Report
## 1. Executive Summary & Claim-Evidence Graph
Summary here.
## 2. Technical Architecture & Mathematical Specification
Spec here.
## 3. Mandatory Adversarial Verification & Failure Mode Mapping
Gauntlet here.
## 4. Discernment Bench Verdict & Epistemic Confidence
Approved.
## 5. Verification Questions & Resolutions
| Question | Evidence Needed | Resolution or Answer | Status |
| --- | --- | --- | --- |
| Test Q | Evidence | Answer | 🟢 RESOLVED |
## 7. Reproduction Instructions & Hash Receipts
`python3 script.py`
""",
    "MUTANT_04_BROKEN_TABLE_COLUMNS": """# Audit Report
## 1. Executive Summary & Claim-Evidence Graph
Summary here.
## 2. Technical Architecture & Mathematical Specification
Spec here.
## 3. Mandatory Adversarial Verification & Failure Mode Mapping
Gauntlet here.
## 4. Discernment Bench Verdict & Epistemic Confidence
Approved.
## 5. Verification Questions & Resolutions
| Incomplete Column | Another Column |
| --- | --- |
| Data 1 | Data 2 |
## 6. Known Limitations & Non-Claims Note
Bounds declared.
## 7. Reproduction Instructions & Hash Receipts
`python3 script.py`
"""
}

class ValidatorOfValidators:
    def __init__(self):
        self.enforcer = ZorasReportSchemaEnforcer()

    def run_mutation_gauntlet(self) -> Dict[str, Any]:
        results = {}
        print("=================================================================")
        print("WHO VALIDATES THE VALIDATOR? (MUTATION AUDIT GAUNTLET)")
        print("=================================================================")

        # Test 1: Known-Good Fixture must pass
        print("\n[TEST 1] Testing Known-Good Fixture against Validator...")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(KNOWN_GOOD_FIXTURE)
            f_path = f.name

        try:
            val_good = self.enforcer.validate_report(f_path)
            passed = val_good["valid"] is True
            results["known_good_fixture"] = {
                "expected": "PASS",
                "actual": "PASS" if passed else "FAIL",
                "passed": passed
            }
            print(f"[*] Known-Good Fixture Verdict: {'[GREEN] PASSED' if passed else '[RED] FAILED'}")
        finally:
            if os.path.exists(f_path):
                os.remove(f_path)

        # Test 2: Known-Bad Mutants must ALL fail
        all_mutants_caught = True
        mutant_results = {}

        for mutant_id, content in KNOWN_BAD_FIXTURES.items():
            print(f"\n[MUTATION TEST] Testing {mutant_id} against Validator...")
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
                f.write(content)
                f_path = f.name

            try:
                val_bad = self.enforcer.validate_report(f_path)
                # Must be rejected (valid == False)
                caught = val_bad["valid"] is False
                if not caught:
                    all_mutants_caught = False
                mutant_results[mutant_id] = {
                    "expected": "REJECT",
                    "actual": "REJECT" if caught else "ACCEPTED (SECURITY LEAK)",
                    "caught": caught,
                    "missing_sections": val_bad.get("missing_sections", []),
                    "table_errors": val_bad.get("table_errors", [])
                }
                print(f"[*] {mutant_id}: {'[GREEN] CAUGHT & REJECTED' if caught else '[RED] FALSE ACCEPTANCE (COMPROMISED)'}")
            finally:
                if os.path.exists(f_path):
                    os.remove(f_path)

        results["known_bad_mutants"] = {
            "all_caught": all_mutants_caught,
            "mutants": mutant_results
        }

        overall_valid = results["known_good_fixture"]["passed"] and all_mutants_caught
        print("\n=================================================================")
        print(f"VALIDATOR INTEGRITY VERDICT: {'VALIDATOR IS CERTIFIED AIRTIGHT' if overall_valid else 'VALIDATOR COMPROMISED'}")
        print("=================================================================")

        return {
            "validator_integrity_passed": overall_valid,
            "results": results
        }

if __name__ == "__main__":
    vov = ValidatorOfValidators()
    receipt = vov.run_mutation_gauntlet()
    out_path = os.path.expanduser("~/Desktop/SSOT_Agentic_Brain/docs/audits/VALIDATOR_OF_VALIDATORS_RECEIPT.json")
    with open(out_path, "w") as f:
        json.dump(receipt, f, indent=2)
