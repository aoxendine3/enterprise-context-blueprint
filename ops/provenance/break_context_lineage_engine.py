#!/usr/bin/env python3
"""
===============================================================================
ADVERSARIAL BREAKER & STRESS GAUNTLET: CONTEXT LINEAGE ENGINE
===============================================================================
Red-Team Breaker script that attempts to exploit, corrupt, and break the
Context Lineage & Execution Provenance Engine under 7 hostile attack modes.

Author: The Lead 9 Council / Xoras Red Team
Date: 2026-09-30
===============================================================================
"""

import os
import sys
import time
import json
import sqlite3
import random
import threading
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from provenance.context_lineage_dag_engine import ContextLineageEngine, DB_PATH

TEST_DB = os.path.expanduser("~/Desktop/SSOT_Agentic_Brain/.sovereign/provenance/test_lineage_breaker.db")

class LineageEngineBreaker:
    def __init__(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        self.engine = ContextLineageEngine(db_path=TEST_DB)
        self.session_id = "adversarial_gauntlet_session"

    def run_all_attack_vectors(self) -> Dict[str, Any]:
        results = {}
        print("=================================================================")
        print("LAUNCHING ADVERSARIAL BREAKER GAUNTLET: CONTEXT LINEAGE ENGINE")
        print("=================================================================")

        # Vector 1: Baseline Clean Build (100 Nodes)
        print("\n[VECTOR 1] Committing 100 sequential clean nodes...")
        for i in range(100):
            self.engine.commit_step(self.session_id, f"agent_{i%5}", "TOOL_EXECUTION", {"step": i, "payload": f"data_{i}"})
        audit_clean = self.engine.verify_lineage(self.session_id)
        results["vector_1_clean_baseline"] = {
            "passed": audit_clean["valid"] and audit_clean["node_count"] == 100,
            "violations": audit_clean["violations"]
        }
        print(f"[*] Baseline Result: Valid={audit_clean['valid']}, Nodes={audit_clean['node_count']}")

        # Vector 2: Direct Database HMAC Signature Tampering
        print("\n[VECTOR 2] Tampering HMAC signature on Node #42...")
        with sqlite3.connect(TEST_DB) as conn:
            cur = conn.cursor()
            cur.execute("SELECT node_id FROM lineage_nodes WHERE session_id = ? ORDER BY timestamp ASC LIMIT 1 OFFSET 42", (self.session_id,))
            target_node = cur.fetchone()[0]
            conn.execute("UPDATE lineage_nodes SET signature = 'FORGED_HMAC_SIGNATURE_0000' WHERE node_id = ?", (target_node,))
            conn.commit()

        audit_tamper = self.engine.verify_lineage(self.session_id)
        sig_caught = any(v.get("error") == "SIGNATURE_MUTATION_DETECTED" for v in audit_tamper["violations"])
        results["vector_2_hmac_tamper"] = {
            "passed": not audit_tamper["valid"] and sig_caught,
            "signature_forgery_caught": sig_caught,
            "violation_details": audit_tamper["violations"]
        }
        print(f"[*] Signature Tampering Caught: {sig_caught} (Valid status={audit_tamper['valid']})")

        # Repair node 42 for subsequent vectors
        with sqlite3.connect(TEST_DB) as conn:
            cur = conn.cursor()
            cur.execute("SELECT node_id, payload_hash FROM lineage_nodes WHERE node_id = ?", (target_node,))
            nid, phash = cur.fetchone()
            repaired_sig = self.engine.compute_hmac(nid, phash)
            conn.execute("UPDATE lineage_nodes SET signature = ? WHERE node_id = ?", (repaired_sig, nid))
            conn.commit()

        # Vector 3: Broken Parent Linkage Attack
        print("\n[VECTOR 3] Forging parent_hash on Node #75...")
        with sqlite3.connect(TEST_DB) as conn:
            cur = conn.cursor()
            cur.execute("SELECT node_id FROM lineage_nodes WHERE session_id = ? ORDER BY timestamp ASC LIMIT 1 OFFSET 75", (self.session_id,))
            target_node_75 = cur.fetchone()[0]
            conn.execute("UPDATE lineage_nodes SET parent_hash = 'FORGED_PARENT_HASH_BAD_LINK' WHERE node_id = ?", (target_node_75,))
            conn.commit()

        audit_parent = self.engine.verify_lineage(self.session_id)
        parent_caught = any(v.get("error") == "BROKEN_PARENT_CHAIN" for v in audit_parent["violations"])
        results["vector_3_parent_chain_break"] = {
            "passed": not audit_parent["valid"] and parent_caught,
            "parent_break_caught": parent_caught,
            "violation_details": audit_parent["violations"]
        }
        print(f"[*] Broken Parent Link Caught: {parent_caught} (Valid status={audit_parent['valid']})")

        # Vector 4: Merkle Root Desync Attack
        print("\n[VECTOR 4] Forging Merkle Root on Session Head...")
        with sqlite3.connect(TEST_DB) as conn:
            conn.execute("UPDATE lineage_nodes SET merkle_root = 'CORRUPTED_MERKLE_ROOT_99999' WHERE session_id = ?", (self.session_id,))
            conn.commit()

        audit_merkle = self.engine.verify_lineage(self.session_id)
        merkle_caught = any(v.get("error") == "MERKLE_ROOT_DESYNC" for v in audit_merkle["violations"])
        results["vector_4_merkle_desync"] = {
            "passed": not audit_merkle["valid"] and merkle_caught,
            "merkle_desync_caught": merkle_caught
        }
        print(f"[*] Merkle Root Corruption Caught: {merkle_caught}")

        # Vector 5: 50-Thread Concurrent Write Stress (Race Condition Test)
        print("\n[VECTOR 5] Launching 50 Concurrent Writer Threads (Race Condition Gauntlet)...")
        race_session = "race_condition_session"
        errors = []

        def worker(thread_idx: int):
            try:
                for j in range(20):
                    self.engine.commit_step(race_session, f"worker_{thread_idx}", "CONCURRENT_WRITE", {"t": thread_idx, "step": j})
            except Exception as e:
                errors.append(str(e))

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(worker, i) for i in range(50)]
            for f in futures:
                f.result()

        audit_race = self.engine.verify_lineage(race_session)
        results["vector_5_concurrent_race"] = {
            "passed": len(errors) == 0 and audit_race["node_count"] == 1000,
            "node_count": audit_race["node_count"],
            "errors_encountered": len(errors),
            "lineage_valid": audit_race["valid"]
        }
        print(f"[*] Concurrent Race Test: Committed={audit_race['node_count']}/1000 nodes, Errors={len(errors)}")

        # Vector 6: High-Scale Burst (5,000 Nodes Throughput Benchmark)
        print("\n[VECTOR 6] Committing 5,000 Node Burst Performance Benchmark...")
        burst_session = "burst_benchmark_session"
        start_t = time.time()
        for k in range(5000):
            self.engine.commit_step(burst_session, "maxx", "BURST_NODE", {"idx": k})
        duration = time.time() - start_t
        ops_sec = 5000.0 / duration if duration > 0 else 0.0

        audit_burst = self.engine.verify_lineage(burst_session)
        results["vector_6_high_scale_burst"] = {
            "passed": audit_burst["valid"] and audit_burst["node_count"] == 5000,
            "total_nodes": audit_burst["node_count"],
            "duration_sec": round(duration, 3),
            "throughput_ops_sec": round(ops_sec, 2),
            "merkle_root": audit_burst["merkle_root"]
        }
        print(f"[*] Burst Benchmark: 5,000 nodes in {duration:.2f}s ({ops_sec:.1f} ops/sec). Merkle Root: {audit_burst['merkle_root'][:16]}...")

        # Summary
        all_passed = all(v["passed"] for v in results.values())
        print("\n=================================================================")
        print(f"BREAKER GAUNTLET VERDICT: {'ALL TEST VECTORS PASSED (AIRTIGHT)' if all_passed else 'FAILURE DETECTED'}")
        print("=================================================================")

        return {
            "gauntlet_passed": all_passed,
            "vectors": results
        }

if __name__ == "__main__":
    breaker = LineageEngineBreaker()
    res = breaker.run_all_attack_vectors()
    with open(os.path.expanduser("~/Desktop/SSOT_Agentic_Brain/docs/audits/CONTEXT_LINEAGE_BREAKER_RECEIPT.json"), "w") as f:
        json.dump(res, f, indent=2)
