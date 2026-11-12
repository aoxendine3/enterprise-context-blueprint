#!/usr/bin/env python3
"""
===============================================================================
XORAS-NATIVE REPORT SCHEMA ENFORCER & VALIDATOR (v1.0.0)
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
import stat
import hashlib
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

# SHA-256 digest pattern (64 lowercase hex chars)
SHA256_RE = re.compile(r"\b[0-9a-f]{64}\b")

class XorasReportSchemaEnforcer:
    def __init__(self, workspace_root: str | None = None):
        self.workspace_root = workspace_root or os.path.expanduser("~/Desktop/SSOT_Agentic_Brain")

    def _extract_sha256_digests(self, content: str) -> List[str]:
        """Extract all SHA-256 digests claimed in a report."""
        return SHA256_RE.findall(content)

    def _verify_evidence_hash_on_disk(self, digest: str) -> Dict[str, Any]:
        """
        Truth check: does the claimed SHA-256 digest match any real on-disk
        file in the workspace? Returns match info or a MISSING_HASH verdict.
        Walks the workspace (skipping heavy residue dirs) looking for a byte-
        exact match so a forged digest cannot pass.
        """
        result = {
            "digest": digest,
            "verified": False,
            "matching_files": [],
            "verdict": "MISSING_HASH",
        }
        # Evidence lives in bounded, known locations. Hash only these so truth
        # verification never runs away into misc/ residue (200k+ files, special
        # files, dot-cloud caches) or hangs on non-regular files.
        evidence_roots = [
            os.path.join(self.workspace_root, "memory"),
            os.path.join(self.workspace_root, "core", "ops"),
            os.path.join(self.workspace_root, "docs", "audits"),
            os.path.join(self.workspace_root, "core", "products"),
            os.path.join(self.workspace_root, "labs", "workspaces"),
            os.path.join(self.workspace_root, "tests"),
            os.path.join(self.workspace_root, "workspaces"),
            os.path.join(self.workspace_root, "barn"),
        ]
        max_file_bytes = 50 * 1024 * 1024
        scanned = 0
        scan_cap = 4000
        for ev_root in evidence_roots:
            if not os.path.isdir(ev_root):
                continue
            for root, dirs, files in os.walk(ev_root):
                dirs[:] = [d for d in dirs if d not in {"node_modules", ".git", ".venv", "__pycache__", "build", "dist"}]
                for fn in files:
                    scanned += 1
                    if scanned > scan_cap:
                        result["verdict"] = "SCAN_CAP_REACHED"
                        return result
                    full = os.path.join(root, fn)
                    try:
                        st = os.stat(full)
                    except OSError:
                        continue
                    if not stat.S_ISREG(st.st_mode):
                        continue
                    if st.st_size > max_file_bytes:
                        continue
                    try:
                        h = hashlib.sha256(open(full, "rb").read()).hexdigest()
                    except (OSError, PermissionError):
                        continue
                    if h == digest:
                        result["verified"] = True
                        result["matching_files"].append(os.path.relpath(full, self.workspace_root))
        if result["verified"]:
            result["verdict"] = "HASH_VERIFIED_ON_DISK"
        return result

    def _extract_repro_command(self, content: str) -> str | None:
        """Extract the reproducibility command from a report (best effort)."""
        m = re.search(r"`python3[^`]*`", content)
        if m:
            return m.group(0).strip("`")
        m2 = re.search(r"python3\s+\S+", content)
        if m2:
            return m2.group(0)
        return None

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

        # --- TRUTH VERIFICATION (new) ---
        # A report must not cite SHA-256 digests that match nothing on disk.
        digests = self._extract_sha256_digests(content)
        hash_verdicts = [self._verify_evidence_hash_on_disk(d) for d in digests]
        unverified_hashes = [v for v in hash_verdicts if not v["verified"]]

        # A reproducibility command, if present, should point at a real script.
        repro_cmd = self._extract_repro_command(content)
        repro_verified = False
        repro_verdict = "NO_REPRO_COMMAND"
        if repro_cmd:
            parts = repro_cmd.split()
            script = parts[-1] if parts else ""
            if os.path.exists(os.path.join(self.workspace_root, script)) or os.path.exists(script):
                repro_verified = True
                repro_verdict = "REPRO_SCRIPT_EXISTS"
            else:
                repro_verdict = "REPRO_SCRIPT_MISSING"

        form_valid = (len(missing_sections) == 0) and table_valid and has_repro_cmd
        truth_valid = (len(unverified_hashes) == 0) and (not repro_cmd or repro_verified)

        return {
            "valid": form_valid and truth_valid,
            "file_path": file_path,
            "missing_sections": missing_sections,
            "table_errors": table_errors,
            "has_repro_cmd": has_repro_cmd,
            "form_valid": form_valid,
            "truth_valid": truth_valid,
            "hash_verdicts": hash_verdicts,
            "unverified_hashes": unverified_hashes,
            "repro_verdict": repro_verdict,
            "repro_verified": repro_verified,
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
    parser = argparse.ArgumentParser(description="XORAS Report Schema Enforcer")
    parser.add_argument("--validate", type=str, help="Path to markdown report file to validate")
    parser.add_argument("--dir", type=str, help="Directory of audit reports to validate")
    args = parser.parse_args()

    enforcer = XorasReportSchemaEnforcer()

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
        print("XORAS REPORT SCHEMA COMPLIANCE AUDIT")
        print("================================================")
        for k, v in res["reports"].items():
            status = "[GREEN] COMPLIANT" if v["valid"] else f"[RED] NON-COMPLIANT (Missing: {v['missing_sections']})"
            print(f"{k}: {status}")
        print("------------------------------------------------")
        print(f"OVERALL VERDICT: {'ALL REPORTS COMPLIANT' if res['overall_valid'] else 'NON-COMPLIANT REPORTS DETECTED'}")
        sys.exit(0 if res["overall_valid"] else 1)

if __name__ == "__main__":
    main()


# Backward-compatibility alias
ZorasReportSchemaEnforcer = XorasReportSchemaEnforcer
