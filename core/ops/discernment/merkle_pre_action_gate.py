import os
import hashlib
import json
from datetime import datetime

# EVE DIRECTIVE: 7th Layer Merkle Pre-Action Gate
# - Tree Structure: Root -> Agent Nodes -> Asset Leaves
# - Friction Flags: Thrown when shallow match chosen over deep/better match
# - Demotion: Shallow losers routed to Barn Archive (Linear Journal)

REGISTRY_ROOT = "memory/tri_brain/merkle_registry"
BARN_JOURNAL = "memory/catch_log/barn_archive/merkle_journal"

class FrictionFlag(Exception):
    pass

def generate_leaf_hash(asset_path):
    # Simulates cryptographic leaf hashing
    return hashlib.sha256(asset_path.encode()).hexdigest()[:16]

def throw_friction_flag(shallow_asset, deep_asset):
    flag_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "FRICTION_FLAG_REVERSION_ATTEMPT",
        "suppressed_signal": shallow_asset,
        "superior_asset_ignored": deep_asset,
        "action": "HALT_AND_ROUTE_TO_BARN"
    }
    
    # Write to Barn Archive Linear Journal
    with open(os.path.join(BARN_JOURNAL, "friction_flags.jsonl"), "a") as f:
        f.write(json.dumps(flag_data) + "\n")
    
    print(f"\n[JARVIS AUDIT] FRICTION FLAG DEPLOYED: Reversion Attempt Caught.")
    print(f" -> Agent attempted to load shallow asset: {shallow_asset}")
    print(f" -> Deeper, superior asset exists: {deep_asset}")
    print(f" -> Action: Shallow asset demoted to Barn. Deep asset enforced.")

def pre_action_gate_check(requested_asset):
    """
    Mandatory 7th-Layer Gate. Runs BEFORE any tool or file touch.
    """
    print(f"[MAXX GATE] Querying Merkle Registry Tree for: {requested_asset}")
    
    # Simulated Registry State (Log-time hash path jumping)
    registry_tree = {
        "parser_legacy": {"depth": 1, "score": 40, "path": "ops/scripts/parser.py"},
        "parser_sovra": {"depth": 6, "score": 99, "path": "workspaces/sovra_sandbox/src/xmars_dag_parser.c"}
    }
    
    # Evaluate Depth vs Score (Friction Template)
    # If the requested asset is shallow and a deeper one scores higher -> FLAG
    
    if requested_asset == "parser_legacy":
        shallow = registry_tree["parser_legacy"]
        deep = registry_tree["parser_sovra"]
        
        if deep["score"] > shallow["score"] and deep["depth"] > shallow["depth"]:
            throw_friction_flag(shallow["path"], deep["path"])
            return deep["path"] # Return the correct asset
            
    print("[MAXX GATE] Asset Approved. No reversion detected.")
    return requested_asset

if __name__ == "__main__":
    os.makedirs(REGISTRY_ROOT, exist_ok=True)
    os.makedirs(BARN_JOURNAL, exist_ok=True)
    
    print("=========================================================================")
    print("           [7TH LAYER] MERKLE PRE-ACTION GATE (EVE DIRECTIVE)            ")
    print("=========================================================================\n")
    
    # Simulate a Cold-Start Reversion Attempt
    print(">>> Agent Action Requested: Load parser logic.")
    print(">>> Agent defaults to shallow match: 'parser_legacy' (Depth 1)\n")
    
    enforced_asset = pre_action_gate_check("parser_legacy")
    
    print(f"\n[SYSTEM] Execution authorized for target: {enforced_asset}")
    print("=========================================================================\n")

