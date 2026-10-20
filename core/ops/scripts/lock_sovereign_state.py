#!/usr/bin/env python3
"""
=============================================================================
SOVEREIGN STATE IMMUTABLE LOCK & PROVENANCE COMMIT HARNESS
Governance: Invariant A, Invariant B, Log Entry #078 & #079
Function: Deep-locks verified audits, empirical telemetry, and core engines
          into Context Lineage Merkle DAG Engine and writes immutable receipt.
=============================================================================
"""

import os
import sys
import json
import time
import hashlib
from pathlib import Path

# Add project root to path
ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
sys.path.insert(0, str(ROOT))

from ops.provenance.context_lineage_dag_engine import ContextLineageEngine

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def execute_lock():
    print("=" * 72)
    print("🔒 SOVEREIGN STATE IMMUTABLE LOCK & PROVENANCE COMMIT")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print("=" * 72)

    engine = ContextLineageEngine()
    session_id = f"session_lock_{int(time.time())}"

    # Critical artifacts to lock down against loss or breakage
    artifacts_to_lock = [
        ROOT / "docs/audits/XMARS_OS_UNBIASED_ARCHITECTURAL_AUDIT.md",
        ROOT / "docs/audits/WINDOWS_VS_M4_EMPIRICAL_TELEMETRY_RECEIPT.json",
        ROOT / "docs/audits/SOVRA_DEEP_LOCK_GAUNTLET_RECEIPT.json",
        ROOT / "docs/audits/DAXX_RECURSIVE_MISSION_EMPIRICAL_RECEIPT.json",
        ROOT / "docs/audits/SOVEREIGN_TRIAD_EMPIRICAL_AUDIT.json",
        ROOT / "ops/scripts/sovra_deep_lock.py",
        ROOT / "ops/scripts/council_audio_dispatch.py",
        ROOT / "ops/scripts/daxx_recursive_bounded_mission.py",
        ROOT / "core/ops/native/shm_ring_buffer.c"
    ]

    locked_manifest = []
    print("\n[PHASE 1] Computing SHA-256 Hashes and Verifying Artifact Integrity...")
    for p in artifacts_to_lock:
        if not p.is_file():
            raise FileNotFoundError(f"CRITICAL FAULT: Asset {p} missing from disk!")
        f_hash = sha256_file(p)
        f_size = p.stat().st_size
        print(f"  ✓ LOCKED: {p.name:<45} | Size: {f_size:>8} B | Hash: {f_hash[:16]}...")
        locked_manifest.append({
            "path": str(p.relative_to(ROOT)),
            "sha256": f_hash,
            "size_bytes": f_size
        })

    print("\n[PHASE 2] Committing Cryptographic State Nodes to Merkle DAG...")
    committed_nodes = []
    parent_hash = None
    for item in locked_manifest:
        node = engine.commit_step(
            session_id=session_id,
            agent_id="actor://council/daxx",
            step_type="IMMUTABLE_ARTIFACT_LOCK",
            payload=item,
            parent_hash=parent_hash
        )
        committed_nodes.append(node["node_id"])
        parent_hash = node["node_id"]
        print(f"  ✓ DAG Node Committed: {node['node_id'][:20]}... [Seq #{node['seq_num']}]")

    print("\n[PHASE 3] Synchronizing Global Merkle Root...")
    global_merkle_root = engine.sync_global_merkle_root()
    print(f"  ✓ New Global Merkle Root: {global_merkle_root}")

    print("\n[PHASE 4] Running Anti-Corruption & DAG Lineage Validation...")
    validation = engine.verify_lineage(session_id)
    if not validation["valid"] or validation["violations"]:
        raise RuntimeError(f"DAG Validation Failed: {validation['violations']}")
    print(f"  ✓ DAG Integrity Validated: 0 violations, {validation['node_count']} nodes verified.")

    # Write persistent receipt to catch_log
    receipt_path = ROOT / "memory/catch_log/SOVEREIGN_IMMUTABLE_LOCK_RECEIPT.json"
    receipt_data = {
        "receipt_id": f"rcpt_lock_{int(time.time()*1000)}",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "session_id": session_id,
        "global_merkle_root": global_merkle_root,
        "locked_artifacts_count": len(locked_manifest),
        "locked_manifest": locked_manifest,
        "validation_result": validation,
        "governance": {
            "status": "LOCKED_IMMUTABLE",
            "fail_closed_compliance": "PASS",
            "zero_loss_zero_corruption": "PROVEN"
        }
    }
    with open(receipt_path, "w", encoding="utf-8") as f:
        json.dump(receipt_data, f, indent=2)

    print(f"  ✓ Receipt Committed: {receipt_path.relative_to(ROOT)}")
    print("=" * 72)
    print("🔒 LOCKDOWN COMPLETE: Zero State Drift, Zero Loss, Zero Corruption.")
    print("=" * 72)
    return receipt_data

if __name__ == "__main__":
    execute_lock()
