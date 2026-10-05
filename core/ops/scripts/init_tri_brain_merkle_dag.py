#!/usr/bin/env python3
"""
XORAS TRI-BRAIN MERKLE CATCH DAG LOCK ENGINE
100% OFF-GRID BARE-METAL BINDING LAW

Locks the Vector-Merkle Catch DAG into all 3 Brain Containers:
  - Container 1 (memory/tri_brain/container_1/): Short-Term Execution & Spoken Audio Receipts
  - Container 2 (memory/tri_brain/container_2/): Long-Term Memory & Poincaré Semantic Folding
  - Container 3 (memory/tri_brain/container_3/): 18,432-D HexCell SIMD Vector Substrate

Replaces legacy flat catch logs with out-of-this-world holographic vector integrity.
"""

import sys
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
MASTER_DAG_FILE = ROOT / "memory" / "catch_log" / "merkle_catch_dag.json"
TRI_BRAIN_ROOT = ROOT / "memory" / "tri_brain"

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def lock_tri_brain_merkle_dag() -> dict:
    if not MASTER_DAG_FILE.exists():
        return {"status": "FAILED", "reason": "Master Merkle Catch DAG missing."}

    master_nodes = json.loads(MASTER_DAG_FILE.read_text(encoding='utf-8'))
    
    # 1. Partition Nodes into 3 Brain Containers based on operational category
    c1_nodes = [] # Speech & Short-Term Execution
    c2_nodes = [] # Long-Term Knowledge & Architecture
    c3_nodes = [] # 18,432-D Vector Embeddings & Heavy Computations

    for node in master_nodes:
        beat = node.get("beat_type", "")
        if beat in ["INTENT", "STATUS", "RESULT", "TRANSITION"]:
            c1_nodes.append(node)
        elif beat in ["CATCH", "GENESIS"]:
            c2_nodes.append(node)
        else:
            c3_nodes.append(node)

    # 2. Write Brain Container DAG Snapshots & Merkle Roots
    results = {}
    for c_id, c_name, nodes in [(1, "container_1", c1_nodes), (2, "container_2", c2_nodes), (3, "container_3", c3_nodes)]:
        c_dir = TRI_BRAIN_ROOT / c_name
        c_dir.mkdir(parents=True, exist_ok=True)
        
        dag_file = c_dir / "merkle_dag.json"
        hash_file = c_dir / "merkle_root.hash"
        
        dag_file.write_text(json.dumps(nodes, indent=2, ensure_ascii=False), encoding='utf-8')
        c_root = nodes[-1]["node_hash"] if nodes else "0"*64
        hash_file.write_text(c_root, encoding='utf-8')
        
        results[c_name] = {
            "node_count": len(nodes),
            "merkle_root": c_root
        }

    # 3. Compute Unified Tri-Brain Master Merkle Root Hash
    master_raw = f"{results['container_1']['merkle_root']}|{results['container_2']['merkle_root']}|{results['container_3']['merkle_root']}"
    unified_root = sha256_text(master_raw)
    
    unified_hash_file = TRI_BRAIN_ROOT / "unified_merkle_root.hash"
    unified_hash_file.write_text(unified_root, encoding='utf-8')

    print("=================================================================")
    print("XORAS TRI-BRAIN MERKLE CATCH DAG LOCK INITIALIZED")
    print("=================================================================")
    print(f"Container 1 (Short-Term & Audio) : {results['container_1']['node_count']} Nodes | Root: {results['container_1']['merkle_root'][:16]}...")
    print(f"Container 2 (Long-Term Fabric)   : {results['container_2']['node_count']} Nodes | Root: {results['container_2']['merkle_root'][:16]}...")
    print(f"Container 3 (18,432-D Vector DB) : {results['container_3']['node_count']} Nodes | Root: {results['container_3']['merkle_root'][:16]}...")
    print("-----------------------------------------------------------------")
    print(f"UNIFIED TRI-BRAIN MERKLE ROOT : {unified_root}")
    print("=================================================================")

    return {
        "status": "GREEN",
        "unified_root": unified_root,
        "containers": results
    }

if __name__ == "__main__":
    lock_tri_brain_merkle_dag()
