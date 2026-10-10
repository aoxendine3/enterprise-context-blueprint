#!/usr/bin/env python3
"""
===============================================================================
XORAS PROVENANCE-AWARE INTAKE GATE & LINEAGE SWEEPER (v2.0)
===============================================================================
Author: The Lead 9 Council / Xoras Systems
Date: 2026-10-05

Function:
1. Fans out across all record-bearing surfaces:
   - Git History (Authoritative Clock)
   - Merkle Logs & Tri-Brain Journals
   - Catch Logs & Provenance DBs
   - Audit V&V Reports
2. Classifies incoming requests/artifacts into 3 strict states:
   - Fully Present (Cited & Reused)
   - Partially Present (Tracked & Reconstructed Lineage)
   - Absent (Flagged, Zero Fabrication)
3. Outputs an immutable Provenance Map prior to task execution.
===============================================================================
"""

import os
import sys
import json
import time
import subprocess
import glob
from typing import Dict, List, Any, Optional

WORKSPACE_ROOT = os.path.expanduser("~/Desktop/SSOT_Agentic_Brain")

class ProvenanceIntakeGate:
    def __init__(self, root_dir: str = WORKSPACE_ROOT):
        self.root_dir = root_dir
        self.provenance_db_path = os.path.join(root_dir, ".sovereign", "provenance", "lineage_dag.db")
        self.tri_brain_dir = os.path.join(root_dir, "memory", "tri_brain")
        self.catch_log_dir = os.path.join(root_dir, "memory", "catch_log")
        self.audits_dir = os.path.join(root_dir, "docs", "audits")

    def get_git_authoritative_clock(self) -> Dict[str, str]:
        """Uses Git commit history as the authoritative clock instead of volatile file mtimes."""
        try:
            cmd = ["git", "log", "-n", "50", "--pretty=format:%H|%an|%ad|%s", "--date=iso-strict"]
            res = subprocess.run(cmd, cwd=self.root_dir, capture_output=True, text=True, check=True)
            commits = []
            for line in res.stdout.strip().split("\n"):
                if line:
                    parts = line.split("|")
                    if len(parts) >= 4:
                        commits.append({
                            "hash": parts[0],
                            "author": parts[1],
                            "date": parts[2],
                            "subject": parts[3]
                        })
            return {"status": "SUCCESS", "latest_commit": commits[0] if commits else None, "history": commits}
        except Exception as e:
            return {"status": "DEGRADED", "error": str(e), "latest_commit": None, "history": []}

    def scan_polyglot_assets(self) -> Dict[str, List[str]]:
        """Scans workspace for native polyglot compiled binaries and substrate libraries (Rust, C++, Zig, Sovra)."""
        polyglot_map = {
            "rust_sources": [],
            "cpp_sources": [],
            "native_dylibs": [],
            "sovra_dsl": []
        }
        for root, _, files in os.walk(self.root_dir):
            if ".venv" in root or ".git" in root or "barn" in root:
                continue
            for f in files:
                rel_path = os.path.relpath(os.path.join(root, f), self.root_dir)
                if f.endswith(".rs"):
                    polyglot_map["rust_sources"].append(rel_path)
                elif f.endswith(".cpp") or f.endswith(".hpp"):
                    polyglot_map["cpp_sources"].append(rel_path)
                elif f.endswith(".dylib") or f.endswith(".so"):
                    polyglot_map["native_dylibs"].append(rel_path)
                elif f.endswith(".sovra"):
                    polyglot_map["sovra_dsl"].append(rel_path)
        return polyglot_map

    def sweep_record_surfaces(self, target_topic: str) -> Dict[str, Any]:
        """Fans out across git, Merkle journals, catch logs, V&V audit documents, and native polyglot assets."""
        git_clock = self.get_git_authoritative_clock()
        
        # 1. Audit V&V Reports
        audit_files = glob.glob(os.path.join(self.audits_dir, "*.md"))
        matched_audits = [f for f in audit_files if target_topic.lower() in open(f, 'r', encoding='utf-8', errors='ignore').read().lower()]
        
        # 2. Catch Logs
        catch_logs = glob.glob(os.path.join(self.catch_log_dir, "*"))
        matched_catch = [f for f in catch_logs if target_topic.lower() in os.path.basename(f).lower()]
        
        # 3. Tri-Brain Merkle Entries
        tri_brain_files = glob.glob(os.path.join(self.tri_brain_dir, "*"))
        
        # 4. Polyglot Substrate Assets
        polyglot_assets = self.scan_polyglot_assets()
        
        return {
            "target_topic": target_topic,
            "git_clock": git_clock["latest_commit"],
            "matched_audits": [os.path.basename(a) for a in matched_audits],
            "matched_catch_logs": [os.path.basename(c) for c in matched_catch],
            "tri_brain_count": len(tri_brain_files),
            "polyglot_assets": polyglot_assets
        }

    def classify_and_map(self, target_topic: str) -> Dict[str, Any]:
        """Classifies request into FULLY_PRESENT, PARTIALLY_PRESENT, or ABSENT."""
        sweep = self.sweep_record_surfaces(target_topic)
        
        has_audits = len(sweep["matched_audits"]) > 0
        has_catch = len(sweep["matched_catch_logs"]) > 0
        
        if has_audits and has_catch:
            disposition = "FULLY_PRESENT"
            action_guidance = "Cite existing evidence artifacts and execute continuous verification regression."
        elif has_audits or has_catch:
            disposition = "PARTIALLY_PRESENT"
            action_guidance = "Track partial lineage pointers, reconstruct lineage, fill gaps."
        else:
            disposition = "ABSENT"
            action_guidance = "Flag as unverified/absent. Zero fabrication. Generate new formal proof."
            
        provenance_map = {
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "authoritative_clock": sweep["git_clock"]["date"] if sweep["git_clock"] else "UNKNOWN",
            "git_commit": sweep["git_clock"]["hash"] if sweep["git_clock"] else "UNKNOWN",
            "target_topic": target_topic,
            "disposition": disposition,
            "action_guidance": action_guidance,
            "evidence_lineage": {
                "v_and_v_audits": sweep["matched_audits"],
                "catch_logs": sweep["matched_catch_logs"],
                "polyglot_assets": sweep["polyglot_assets"]
            }
        }
        return provenance_map

if __name__ == "__main__":
    gate = ProvenanceIntakeGate()
    topic = sys.argv[1] if len(sys.argv) > 1 else "Consensus"
    pmap = gate.classify_and_map(topic)
    print(json.dumps(pmap, indent=2))
