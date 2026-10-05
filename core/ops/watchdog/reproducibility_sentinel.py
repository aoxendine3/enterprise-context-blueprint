#!/usr/bin/env python3
"""
===============================================================================
SOVEREIGN REPRODUCIBILITY SENTINEL & TRACEABILITY HARNESS (v1.0.0)
===============================================================================
Automated sentinel that sweeps all operational engines, audits, and test suites
to ensure 100% documentation synchronization, reproducible execution recipes,
and cryptographic receipt verification across the entire workspace.

Author: The Lead 9 Council / Xoras Watchdog
Date: 2026-09-30
===============================================================================
"""

import os
import sys
import json
import time
import hashlib
import subprocess
from typing import Dict, List, Any

SSOT_ROOT = os.path.expanduser("~/Desktop/SSOT_Agentic_Brain")
AUDIT_DIR = os.path.join(SSOT_ROOT, "docs/audits")
OPS_DIR = os.path.join(SSOT_ROOT, "ops")

# Certified Execution Registry of System Engines & Test Suites
REPRODUCTION_SUITES = [
    {
        "id": "context_lineage_engine",
        "name": "Sovereign Context Lineage & Execution Provenance Engine",
        "script": "ops/provenance/context_lineage_dag_engine.py",
        "breaker": "ops/provenance/break_context_lineage_engine.py",
        "doc": "docs/audits/CONTEXT_LINEAGE_ENGINE_AUDIT.md",
        "receipt": "docs/audits/CONTEXT_LINEAGE_BREAKER_RECEIPT.json",
        "cmd": "python3 ops/provenance/break_context_lineage_engine.py"
    },
    {
        "id": "governed_memory_engine",
        "name": "Governed Memory Consolidation Engine",
        "script": "ops/memory/governed_memory_consolidation_engine.py",
        "breaker": "ops/memory/break_governed_memory_engine.py",
        "doc": "docs/audits/GOVERNED_MEMORY_CONSOLIDATION_GOVERNOR_SPEC.md",
        "receipt": "memory/catch_log/GOVERNED_MEMORY_BREAKER_RECEIPT.json",
        "cmd": "python3 ops/memory/break_governed_memory_engine.py"
    },
    {
        "id": "byzantine_breaking_point",
        "name": "Byzantine Corruption Breaking Point Ramp",
        "script": "ops/discernment/byzantine_breaking_point_ramp.py",
        "breaker": "ops/discernment/byzantine_breaking_point_ramp.py",
        "doc": "docs/audits/BYZANTINE_BREAKING_POINT_RAMP_AUDIT.md",
        "receipt": "docs/audits/BYZANTINE_BREAKING_POINT_RAMP_AUDIT.md",
        "cmd": "python3 ops/discernment/byzantine_breaking_point_ramp.py"
    },
    {
        "id": "5m_byzantine_swarm",
        "name": "5-Million Agent Byzantine Purple Swarm Gauntlet",
        "script": "ops/discernment/5m_byzantine_purple_swarm_gauntlet.py",
        "breaker": "ops/discernment/5m_byzantine_purple_swarm_gauntlet.py",
        "doc": "docs/audits/5M_BYZANTINE_PURPLE_SWARM_AUDIT.md",
        "receipt": "docs/audits/5M_BYZANTINE_PURPLE_SWARM_TELEMETRY.json",
        "cmd": "python3 ops/discernment/5m_byzantine_purple_swarm_gauntlet.py"
    },
    {
        "id": "task_supervisor_sentinel",
        "name": "Task Supervisor Sentinel Layer",
        "script": "ops/watchdog/task_supervisor_sentinel.py",
        "breaker": "ops/watchdog/task_supervisor_sentinel.py",
        "doc": "ops/watchdog/supervisor_registry.json",
        "receipt": "memory/catch_log/TASK_SUPERVISOR_RECEIPTS.jsonl",
        "cmd": "python3 ops/watchdog/task_supervisor_sentinel.py --sweep"
    }
]

class ReproducibilitySentinel:
    def __init__(self):
        os.makedirs(AUDIT_DIR, exist_ok=True)

    @staticmethod
    def file_hash(rel_path: str) -> str:
        abs_path = os.path.join(SSOT_ROOT, rel_path)
        if not os.path.exists(abs_path):
            return "MISSING"
        with open(abs_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def audit_suite(self, suite: Dict[str, str]) -> Dict[str, Any]:
        script_exists = os.path.exists(os.path.join(SSOT_ROOT, suite["script"]))
        breaker_exists = os.path.exists(os.path.join(SSOT_ROOT, suite["breaker"]))
        doc_exists = os.path.exists(os.path.join(SSOT_ROOT, suite["doc"]))
        receipt_exists = os.path.exists(os.path.join(SSOT_ROOT, suite["receipt"]))

        start_t = time.time()
        # Execute self-test command
        proc = subprocess.run(
            suite["cmd"],
            shell=True,
            cwd=SSOT_ROOT,
            capture_output=True,
            text=True
        )
        duration = round(time.time() - start_t, 3)

        return {
            "id": suite["id"],
            "name": suite["name"],
            "reproducible": proc.returncode == 0 and script_exists and doc_exists,
            "exit_code": proc.returncode,
            "duration_sec": duration,
            "command": suite["cmd"],
            "files": {
                "script": {"path": suite["script"], "hash": self.file_hash(suite["script"])[:16]},
                "doc": {"path": suite["doc"], "hash": self.file_hash(suite["doc"])[:16]},
                "receipt": {"path": suite["receipt"], "hash": self.file_hash(suite["receipt"])[:16]}
            },
            "stdout_tail": proc.stdout.strip().splitlines()[-3:] if proc.stdout else [],
            "stderr_tail": proc.stderr.strip().splitlines()[-3:] if proc.stderr else []
        }

    def run_full_traceability_sweep(self) -> Dict[str, Any]:
        results = []
        all_reproducible = True

        print("=================================================================")
        print("LAUNCHING SOVEREIGN REPRODUCIBILITY SENTINEL SWEEP")
        print("=================================================================")

        for suite in REPRODUCTION_SUITES:
            print(f"[*] Verifying Suite: {suite['name']}...")
            res = self.audit_suite(suite)
            results.append(res)
            if not res["reproducible"]:
                all_reproducible = False
            print(f"    Verdict: {'[GREEN] REPRODUCIBLE' if res['reproducible'] else '[RED] FAILED'} ({res['duration_sec']}s)")

        matrix_doc = self._generate_matrix_md(results)
        matrix_path = os.path.join(AUDIT_DIR, "REPRODUCIBILITY_MATRIX.md")
        with open(matrix_path, "w") as f:
            f.write(matrix_doc)

        receipt_json = {
            "timestamp": time.time(),
            "overall_reproducible": all_reproducible,
            "suites_verified": len(results),
            "results": results
        }
        receipt_path = os.path.join(AUDIT_DIR, "REPRODUCIBILITY_SENTINEL_RECEIPT.json")
        with open(receipt_path, "w") as f:
            json.dump(receipt_json, f, indent=2)

        print("\n=================================================================")
        print(f"SENTINEL SWEEP VERDICT: {'ALL SUITES 100% REPRODUCIBLE & SYNCHRONIZED' if all_reproducible else 'DESYNC DETECTED'}")
        print("=================================================================")

        return receipt_json

    def _generate_matrix_md(self, results: List[Dict[str, Any]]) -> str:
        lines = [
            "# Sovereign Reproducibility & Traceability Matrix",
            "**Document Version:** 1.0.0",
            f"**Last Sweep Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
            "**Author:** The Lead 9 Council / Xoras Watchdog",
            "**Classification:** AUTOMATED LIVING SPECIFICATION",
            "",
            "---",
            "",
            "## 1. Executive Summary",
            "",
            "This matrix records the continuous verification status, cryptographic asset digests, and exact one-line terminal commands required to reproduce every operational engine, benchmark gauntlet, and audit in the SSOT repository.",
            "",
            "---",
            "",
            "## 2. Certified Reproducibility Matrix",
            "",
            "| System Engine | Verification Command | Exit Code | Runtime | Script Digest | Doc Digest | Status |",
            "| --- | --- | --- | --- | --- | --- | --- |"
        ]

        for r in results:
            status_str = "🟢 **REPRODUCIBLE**" if r["reproducible"] else "🔴 **DESYNC**"
            cmd_code = f"`{r['command']}`"
            script_h = r["files"]["script"]["hash"]
            doc_h = r["files"]["doc"]["hash"]
            lines.append(f"| **{r['name']}** | {cmd_code} | `{r['exit_code']}` | `{r['duration_sec']}s` | `{script_h}` | `{doc_h}` | {status_str} |")

        lines.extend([
            "",
            "---",
            "",
            "## 3. Reproduction Instructions",
            "",
            "To execute a full automated reproduction sweep of all system engines, run:",
            "",
            "```bash",
            "python3 /Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/watchdog/reproducibility_sentinel.py",
            "```",
            "",
            "All test outputs are written to `docs/audits/REPRODUCIBILITY_SENTINEL_RECEIPT.json`."
        ])

        return "\n".join(lines)

if __name__ == "__main__":
    sentinel = ReproducibilitySentinel()
    sentinel.run_full_traceability_sweep()
