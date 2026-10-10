#!/usr/bin/env python3
"""
===============================================================================
XORAS::OS — DETERMINISTIC DOCUMENTATION LINT GATE (v1.0.0)
===============================================================================
Enforces a 3-stage formalization pass between raw agent output and customer-facing
engineering documentation:

STAGE 1 (STRIP): Flags theatrical language, mythic framing, and self-promotion.
STAGE 2 (VERIFY): Ensures every numerical claim includes a valid file citation
                 and benchmark harness reference.
STAGE 3 (RESTATE): Provides standard, measured corporate engineering alternatives.
===============================================================================
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Any

# Banned vocabulary & theatrical terms mapped to measured engineering restatements
BANNED_THEATRICAL_TERMS = {
    r"\bsovereign intelligence\b": "isolated autonomous agent system",
    r"\babsolute mathematical truth\b": "formal invariant verification (UNSAT proof)",
    r"\bcatastrophic boundary\b": "performance degradation threshold",
    r"\blead 9 council does not patch\b": "architecture replaces legacy polling with bare-metal gates",
    r"\bsacred core\b": "core operational directory (/core/)",
    r"\bflawless\b": "verified against test suite",
    r"\bzero defect seal\b": "passed automated V&V test gauntlet",
    r"\bgod mode\b": "privileged kernel access mode",
    r"\bapocalyptic\b": "high-stress adversarial",
    r"\bunassailable\b": "formally verified under stated threat model",
    r"\bmythic\b": "high-density",
    r"\bdivine\b": "hardware-isolated",
}

# Regex to identify un-cited numerical claims (e.g. 14 million, 18,432-D, 99.9%)
NUMERICAL_CLAIM_REGEX = re.compile(
    r"(\b\d{1,3}(?:,\d{3})+\b|\b\d+(?:\.\d+)?\s*(?:million|billion|ops/sec|reads/sec|ns|us|ms|D|dimensional|GB|MB|%)\b)"
)

# File citation format requirement: file://... or [label](file://...)
FILE_CITATION_REGEX = re.compile(r"file://[^\s\)]+|\[[^\]]+\]\(file://[^\s\)]+\)")

class DocumentationLintGate:
    def __init__(self, target_file: Path):
        self.target_file = target_file
        self.lines: List[str] = []
        if target_file.exists():
            with open(target_file, "r", encoding="utf-8") as f:
                self.lines = f.readlines()

    def run_stage_1_strip_theatrical(self) -> List[Dict[str, Any]]:
        """Stage 1: Detect theatrical/mythic vocabulary and propose measured restatements."""
        violations = []
        for line_num, line in enumerate(self.lines, start=1):
            for pattern, replacement in BANNED_THEATRICAL_TERMS.items():
                matches = re.findall(pattern, line, flags=re.IGNORECASE)
                if matches:
                    violations.append({
                        "line": line_num,
                        "type": "THEATRICAL_VOCABULARY",
                        "detected": matches[0],
                        "suggested_restatement": replacement,
                        "raw_line": line.strip()
                    })
        return violations

    def run_stage_2_verify_citations(self) -> List[Dict[str, Any]]:
        """Stage 2: Ensure numerical claims have file citations in proximity."""
        violations = []
        for line_num, line in enumerate(self.lines, start=1):
            num_matches = NUMERICAL_CLAIM_REGEX.findall(line)
            if num_matches:
                has_citation = bool(FILE_CITATION_REGEX.search(line))
                # Check adjacent lines (+/- 2 lines) for citations
                if not has_citation:
                    window_start = max(0, line_num - 3)
                    window_end = min(len(self.lines), line_num + 2)
                    window_text = "".join(self.lines[window_start:window_end])
                    has_citation = bool(FILE_CITATION_REGEX.search(window_text))

                if not has_citation:
                    violations.append({
                        "line": line_num,
                        "type": "UNCITED_NUMERICAL_CLAIM",
                        "claim_detected": num_matches[0],
                        "requirement": "Numerical claims must include a file:// citation to benchmark/source code.",
                        "raw_line": line.strip()
                    })
        return violations

    def generate_audit_report(self) -> Dict[str, Any]:
        """Generates structured JSON audit report for the markdown file."""
        stage1_violations = self.run_stage_1_strip_theatrical()
        stage2_violations = self.run_stage_2_verify_citations()
        
        passed = (len(stage1_violations) == 0 and len(stage2_violations) == 0)
        
        return {
            "target_file": str(self.target_file),
            "status": "PASS" if passed else "FAIL",
            "total_lines": len(self.lines),
            "stage_1_theatrical_violations": len(stage1_violations),
            "stage_2_uncited_claims": len(stage2_violations),
            "violations": stage1_violations + stage2_violations
        }

def lint_file(filepath: str):
    p = Path(filepath)
    if not p.exists():
        print(f"Error: File {filepath} does not exist.")
        sys.exit(1)
    linter = DocumentationLintGate(p)
    report = linter.generate_audit_report()
    print(json.dumps(report, indent=2))
    return report["status"] == "PASS"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: doc_lint_gate.py <path_to_markdown_file>")
        sys.exit(1)
    success = lint_file(sys.argv[1])
    sys.exit(0 if success else 1)
