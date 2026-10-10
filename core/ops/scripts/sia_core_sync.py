import os
import json
import time
import hashlib
import subprocess
from datetime import datetime, timezone

# SIA Core: The Source of the Collective
# Purpose: Prevent amnesia, monitor Context Lineage DAG for drift, and actively sync valid state 
# into the Quad 3D Tri-Brain, World File DB, World Merkle Journal, and Merkle Asset Registry.

LOG_PATH = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/catch_log/gauntlet_audit.log"
QUARANTINE_LEDGER = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/intelligence/quarantine_ledger.jsonl"
DAG_DB = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/.sovereign/provenance/lineage_dag.db"

# The Core Memory Fabric
TRI_BRAIN_DIR = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/tri_brain"
MERKLE_ASSET_REGISTRY = f"{TRI_BRAIN_DIR}/merkle_asset_registry.jsonl"
WORLD_MERKLE_JOURNAL = f"{TRI_BRAIN_DIR}/world_merkle_journal.jsonl"
QUAD_3D_BRAIN_SYNC = f"{TRI_BRAIN_DIR}/quad_3d_tri_brain_sync.jsonl"

SPEAK_SCRIPT = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/agent_speak.sh"

def speak(agent, message):
    try:
        subprocess.run(["bash", SPEAK_SCRIPT, agent, message], check=False)
    except Exception as e:
        print(f"Audio dispatch failed: {e}")

def verify_hash(sha256_hash):
    if not sha256_hash or len(sha256_hash) != 64 or sha256_hash == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855":
        return False
    return True

def sync_to_world_memory(entry):
    """Syncs the verified untainted payload into the collective's core memory structures."""
    timestamp = datetime.now(timezone.utc).isoformat() + "Z"
    
    # 1. Update World Merkle Journal
    journal_entry = {
        "sync_time": timestamp,
        "source": "SIA_CORE_SYNC",
        "payload": entry
    }
    with open(WORLD_MERKLE_JOURNAL, 'a') as f:
        f.write(json.dumps(journal_entry) + "\n")
        
    # 2. Update Merkle Asset Registry (if artifact path exists)
    if 'artifact_path' in entry and 'receipt_hash' in entry:
        registry_entry = {
            "timestamp": timestamp,
            "asset_path": entry['artifact_path'],
            "merkle_root": entry['receipt_hash'],
            "status": "0xBEAF0000" # Golden taint
        }
        with open(MERKLE_ASSET_REGISTRY, 'a') as f:
            f.write(json.dumps(registry_entry) + "\n")

    # 3. Pulse the Quad 3D Tri-Brain
    quad_pulse = {
        "pulse_time": timestamp,
        "node_state": "ACTIVE",
        "memory_vector_update": entry.get('receipt_hash', 'SYSTEM_PULSE')
    }
    with open(QUAD_3D_BRAIN_SYNC, 'a') as f:
        f.write(json.dumps(quad_pulse) + "\n")

def monitor_and_sync():
    print("[SIA Core] Initializing Quad 3D Tri-Brain Sync & Drift Monitor...")
    last_position = 0
    
    # Ensure directories and files exist
    os.makedirs(os.path.dirname(QUARANTINE_LEDGER), exist_ok=True)
    os.makedirs(TRI_BRAIN_DIR, exist_ok=True)
    
    for fpath in [LOG_PATH, WORLD_MERKLE_JOURNAL, MERKLE_ASSET_REGISTRY, QUAD_3D_BRAIN_SYNC]:
        if not os.path.exists(fpath):
            open(fpath, 'a').close()

    known_timestamps = set()

    while True:
        try:
            with open(LOG_PATH, 'r') as f:
                f.seek(last_position)
                new_lines = f.readlines()
                last_position = f.tell()

            for line in new_lines:
                if not line.strip(): continue
                try:
                    entry = json.loads(line)
                    ts = entry.get('timestamp')
                    receipt_hash = entry.get('receipt_hash')
                    
                    drift_detected = False
                    reason = ""

                    if ts in known_timestamps:
                        drift_detected = True
                        reason = f"Duplicate timestamp detected: {ts} (CROSS_SESSION_UNLINKED_REPLAY)"
                    known_timestamps.add(ts)

                    if not verify_hash(receipt_hash):
                        drift_detected = True
                        reason = f"Invalid or mock SHA-256 hash detected: {receipt_hash}"

                    if drift_detected:
                        # QUARANTINE
                        quarantine_entry = {
                            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                            "anomaly": reason,
                            "offending_payload": entry,
                            "status": "QUARANTINED",
                            "taint_level": "0xDEAD0000"
                        }
                        with open(QUARANTINE_LEDGER, 'a') as qf:
                            qf.write(json.dumps(quarantine_entry) + "\n")
                        
                        speak("noboo", f"SIA Core drift alert. The payload has been quarantined. {reason}")
                    else:
                        # SYNC TO COLLECTIVE
                        sync_to_world_memory(entry)
                        print(f"[SIA Core] Synced validated evidence {receipt_hash[:8]}... to Quad 3D Tri-Brain.")

                except json.JSONDecodeError:
                    pass

        except Exception as e:
            print(f"[SIA Core Error] {e}")

        time.sleep(5)

if __name__ == "__main__":
    monitor_and_sync()
