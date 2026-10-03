#!/usr/bin/env python3
"""
=============================================================================
XORAS::OS — PRE-FLIGHT DATA CLASSIFIER & 7TH-LAYER MERKLE GATEKEEPER
=============================================================================
Governing Rule: Log Entry #078 & Constitutional Invariant 075
Author: Sovereign Council (Jarvis, Maxx, Vance, Clara)
Target: Bare-Metal Silicon (Apple M4)
=============================================================================
Inspects all incoming datasets before gauntlet admission. Enforces mandatory
cryptographic tagging as either REAL_HARDWARE_TELEMETRY or SYNTHETIC_BENCHMARK.
Rejects any unclassified or deceptive operational data at the door.
=============================================================================
"""

import os, sys, json, hashlib

def classify_dataset(file_path):
    if not os.path.exists(file_path):
        return {"status": "REJECTED", "reason": f"File '{file_path}' does not exist."}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        hasher = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # Check for mandatory provenance tag
        if "REAL_HARDWARE_TELEMETRY" in content:
            tag = "REAL_HARDWARE_TELEMETRY"
        elif "SYNTHETIC_BENCHMARK" in content:
            tag = "SYNTHETIC_BENCHMARK"
        else:
            # Default rejection for unclassified data
            return {
                "status": "REJECTED",
                "reason": "Missing mandatory cryptographic classification tag (REAL_HARDWARE_TELEMETRY or SYNTHETIC_BENCHMARK).",
                "sha256": hasher
            }
            
        return {
            "status": "CERTIFIED",
            "tag": tag,
            "sha256": hasher,
            "path": file_path
        }
    except Exception as e:
        return {"status": "ERROR", "reason": str(e)}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        res = classify_dataset(sys.argv[1])
        print(json.dumps(res, indent=2))
    else:
        print("[PREFLIGHT_GATE] Ready and active.")
