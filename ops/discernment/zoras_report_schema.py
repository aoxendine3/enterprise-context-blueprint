#!/usr/bin/env python3
"""
===============================================================================
ZORAS-NATIVE REPORT SCHEMA ENFORCER & VALIDATOR (v1.0.0)
===============================================================================
Enforces mandatory structural compliance for all audit reports, technical specs,
and benchmark documents written under the SSOT workspace.

Required Sections:
1. Executive Summary & Claim-Evidence Graph
2. Technical Architecture & Mathematical Specification
3. Mandatory Adversarial Verification & Failure Mode Mapping
4. Discernment Bench Verdict & Epistemic Confidence
5. Verification Questions & Resolutions (Table: Question | Evidence Needed | Resolution or Answer | Status)
6. Known Limitations & Non-Claims Note
7. Reproduction Instructions & Hash Receipts

Author: The Lead 9 Council / Xoras Discernment Bench
Date: 2026-09-30
===============================================================================
"""

import os
import sys
import re
import json
import argparse
from typing import Dict, List, Any, Tuple

REQUIRED_SECTIONS = [
    r"Executive Summary",
    r"Technical Architecture|Mathematical Specification",
    r"Adversarial Verification|Failure Mode",
    r"Discernment Bench|Epistemic",
    r"Verification Questions.*Resolutions",
    r"Known Limitations.*Non-Claims",
    r"Reproduction Instructions|Hash Receipts"
]

REQUIRED_TABLE_COLUMNS = [
    "Question",
    "Evidence Needed",
    "Resolution or Answer",
    "Status"
]

class ZorasReportSchemaEnforcer:
    def __init__(self):
        pass

    def validate_report(self, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            return {
                "valid": False,
                "file_path": file_path,
                "error": "FILE_NOT_FOUND",
                "missing_sections": REQUIRED_SECTIONS
            }

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        missing_sections = []
        for sec_pattern in REQUIRED_SECTIONS:
            if not re.search(sec_pattern, content, re.IGNORECASE):
                missing_sections.append(sec_pattern)

        # Check for Verification Questions & Resolutions Table Structure
        table_valid = True
        table_errors = []
        if "Verification Questions" in content or "Resolutions" in content:
            for col in REQUIRED_TABLE_COLUMNS:
                if col not in content:
                    table_valid = False
                    table_errors.append(f"MISSING_COLUMN_{col.upper().replace(' ', '_')}")
        else:
            table_valid = False
            table_errors.append("MISSING_VERIFICATION_TABLE")

        # Check for Reproducibility Command or Code Blocks
        has_repro_cmd = ("reproduc" in content.lower() or "python3" in content) and ("`" in content or "```" in content)

        is_valid = (len(missing_sections) == 0) and table_valid and has_repro_cmd

        return {
            "valid": is_valid,
            "file_path": file_path,
            "missing_sections": missing_sections,
            "table_errors": table_errors,
            "has_repro_cmd": has_repro_cmd
        }

    def validate_audit_directory(self, dir_path: str) -> Dict[str, Any]:
        results = {}
        all_valid = True

        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith(".md"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, os.path.expanduser("~/Desktop/SSOT_Agentic_Brain"))
                    val = self.validate_report(full_path)
                    results[rel_path] = val
                    if not val["valid"]:
                        all_valid = False

        return {
            "overall_valid": all_valid,
            "reports": results
        }

def main():
    parser = argparse.ArgumentParser(description="ZORAS Report Schema Enforcer")
    parser.add_argument("--validate", type=str, help="Path to markdown report file to validate")
    parser.add_argument("--dir", type=str, help="Directory of audit reports to validate")
    args = parser.parse_args()

    enforcer = ZorasReportSchemaEnforcer()

    if args.validate:
        res = enforcer.validate_report(args.validate)
        print(json.dumps(res, indent=2))
        sys.exit(0 if res["valid"] else 1)
    elif args.dir:
        res = enforcer.validate_audit_directory(args.dir)
        print(json.dumps(res, indent=2))
        sys.exit(0 if res["overall_valid"] else 1)
    else:
        # Default behavior: audit docs/audits/
        audit_dir = os.path.expanduser("~/Desktop/SSOT_Agentic_Brain/docs/audits")
        res = enforcer.validate_audit_directory(audit_dir)
        print("================================================")
        print("ZORAS REPORT SCHEMA COMPLIANCE AUDIT")
        print("================================================")
        for k, v in res["reports"].items():
            status = "[GREEN] COMPLIANT" if v["valid"] else f"[RED] NON-COMPLIANT (Missing: {v['missing_sections']})"
            print(f"{k}: {status}")
        print("------------------------------------------------")
        print(f"OVERALL VERDICT: {'ALL REPORTS COMPLIANT' if res['overall_valid'] else 'NON-COMPLIANT REPORTS DETECTED'}")
        sys.exit(0 if res["overall_valid"] else 1)

if __name__ == "__main__":
    main()
