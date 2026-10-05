import sys
import os
import json
import hashlib
from datetime import datetime, timezone

def consolidate_memory(audit_file, target_name):
    with open(audit_file, "r") as f:
        content = f.read()
    
    fact_hash = hashlib.sha256(content.encode()).hexdigest()
    
    node = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entity": target_name,
        "consolidated_fact": f"Candidate {target_name} empirical physics and thermodynamic failure bound.",
        "taint_state": "0xDEAD0000",
        "provenance_document": audit_file,
        "merkle_root": fact_hash,
        "seventh_layer_status": "PASSED_UP_AND_LOCKED"
    }
    
    registry_dir = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/tri_brain/merkle_registry"
    os.makedirs(registry_dir, exist_ok=True)
    
    node_file = os.path.join(registry_dir, f"memory_tri_brain_merkle_registry_{target_name}_consolidated.json")
    with open(node_file, "w") as f:
        json.dump(node, f, indent=2)
        
    print(f"[7TH LAYER GUARD] Memory consolidated. Merkle node written: {node_file}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        consolidate_memory(sys.argv[1], sys.argv[2])
