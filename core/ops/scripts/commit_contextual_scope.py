#!/usr/bin/env python3
"""
=============================================================================
XORAS CONTEXTUAL SCOPE COMMIT & LINEAGE FREEZE
Codifies the current operational state into the Context Lineage Merkle DAG Engine.
=============================================================================
"""

import os
import sys
import json
import hashlib
from pathlib import Path

# Add project root to sys.path
ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
sys.path.insert(0, str(ROOT))

from ops.provenance.context_lineage_dag_engine import ContextLineageEngine

def main():
    engine = ContextLineageEngine()
    session_id = "session_upgp_kernel_v5_freeze"

    # Load receipts and compute digests
    receipt_path = ROOT / "memory/catch_log/XORAS_031_TWO_LAYER_WINDOWS_REPLAY_RECEIPT.json"
    with open(receipt_path, "r") as f:
        receipt_data = json.load(f)
    receipt_digest = hashlib.sha256(json.dumps(receipt_data, sort_keys=True).encode()).hexdigest()

    vnv_doc_path = ROOT / "docs/audits/XORAS_031_TWO_LAYER_KERNEL_INVARIANT_SEPARATION_V_AND_V.md"
    with open(vnv_doc_path, "rb") as f:
        vnv_digest = hashlib.sha256(f.read()).hexdigest()

    context_payload = {
        "context_scope_name": "UPGP_TWO_LAYER_KERNEL_INVARIANT_FROZEN_BASELINE",
        "posture": "ARCHITECTURE_FROZEN_FAIL_CLOSED",
        "ssot_git_commit": "01128fc",
        "proving_ground_git_commit": "bded3b0",
        "canonical_memory_slot": "0x3000",
        "canonical_mass": 18432.000,
        "pre_state_hash": "a7d16584d668d9a1ed4f579228c551a86d66d89a4d29eef3ecea616564be2652",
        "post_state_hash": "a7d16584d668d9a1ed4f579228c551a86d66d89a4d29eef3ecea616564be2652",
        "poincare_invariant_ceiling": 0.5000,
        "mmu_hardware_protection": "PAGE_READONLY / PROT_READ",
        "vnv_document_id": "XORAS-TM-2026-031",
        "vnv_document_sha256": vnv_digest,
        "replay_receipt_sha256": receipt_digest,
        "operational_directive": "INDEPENDENT_FALSIFICATION_ONLY",
        "council_author": "council://lead9/maxx"
    }

    # Commit step to DAG engine
    node = engine.commit_step(
        session_id=session_id,
        agent_id="council://maxx",
        step_type="CONTEXTUAL_SCOPE_FREEZE",
        payload=context_payload
    )

    # Calculate Merkle Root
    session_merkle_root = engine.calculate_merkle_root(session_id)
    global_merkle_root = engine.sync_global_merkle_root()

    print("=" * 70)
    print("🔒 CONTEXTUAL SCOPE CRYPTOGRAPHIC COMMIT ESTABLISHED")
    print("=" * 70)
    print(f"Session ID           : {session_id}")
    print(f"Node ID              : {node['node_id']}")
    print(f"Sequence Number      : #{node['seq_num']}")
    print(f"Parent Hash          : {node['parent_hash']}")
    print(f"Payload Digest       : {node['payload_hash']}")
    print(f"HMAC Signature       : {node['signature']}")
    print(f"Session Merkle Root  : {session_merkle_root}")
    print(f"Global Merkle Root   : {global_merkle_root}")
    print("=" * 70)

    # Persist receipt
    receipt = {
        "context_scope": "UPGP_TWO_LAYER_KERNEL_INVARIANT_FROZEN_BASELINE",
        "session_id": session_id,
        "node_id": node["node_id"],
        "seq_num": node["seq_num"],
        "parent_hash": node["parent_hash"],
        "payload_hash": node["payload_hash"],
        "signature": node["signature"],
        "session_merkle_root": session_merkle_root,
        "global_merkle_root": global_merkle_root,
        "context_payload": context_payload
    }

    receipt_file = ROOT / "memory/catch_log/CONTEXTUAL_SCOPE_FREEZE_RECEIPT.json"
    with open(receipt_file, "w") as f:
        json.dump(receipt, f, indent=2)

    print(f"Receipt written to: {receipt_file}")

if __name__ == "__main__":
    main()
