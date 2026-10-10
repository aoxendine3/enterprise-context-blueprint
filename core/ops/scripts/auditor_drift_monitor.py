import os
import json
import time
import hashlib
import subprocess
from datetime import datetime, timezone

# Sentinel & Auditor Drift Monitor (NoBoo & SIA Core)
# Purpose: Prevent amnesia, monitor Context Lineage DAG for drift, and quarantine faked evidence.

LOG_PATH = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/catch_log/gauntlet_audit.log"
QUARANTINE_LEDGER = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/intelligence/quarantine_ledger.jsonl"
DAG_DB = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/.sovereign/provenance/lineage_dag.db"
SPEAK_SCRIPT = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/agent_speak.sh"

def speak(agent, message):
    try:
        subprocess.run(["bash", SPEAK_SCRIPT, agent, message], check=False)
    except Exception as e:
        print(f"Audio dispatch failed: {e}")

def verify_hash(sha256_hash):
    # Falsification check: empty or invalid hashes
    if not sha256_hash or len(sha256_hash) != 64 or sha256_hash == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855":
        return False
    return True

def monitor_drift():
    print("[SIA Core] Initializing Drift Monitor...")
    last_position = 0
    
    # Ensure files exist
    os.makedirs(os.path.dirname(QUARANTINE_LEDGER), exist_ok=True)
    if not os.path.exists(LOG_PATH):
        open(LOG_PATH, 'a').close()

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

                    # 1. Check for pre-dated or duplicated timestamps (Replay Invariant)
                    if ts in known_timestamps:
                        drift_detected = True
                        reason = f"Duplicate timestamp detected: {ts} (CROSS_SESSION_UNLINKED_REPLAY)"
                    known_timestamps.add(ts)

                    # 2. Check for empty or mock SHA-256 (Falsification check)
                    if not verify_hash(receipt_hash):
                        drift_detected = True
                        reason = f"Invalid or mock SHA-256 hash detected: {receipt_hash}"

                    # 3. Quarantine if drifted
                    if drift_detected:
                        quarantine_entry = {
                            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                            "anomaly": reason,
                            "offending_payload": entry,
                            "status": "QUARANTINED",
                            "taint_level": "0xDEAD0000"
                        }
                        with open(QUARANTINE_LEDGER, 'a') as qf:
                            qf.write(json.dumps(quarantine_entry) + "\n")
                        
                        speak("noboo", f"SIA Core has detected artifact drift. The payload has been quarantined and tainted. {reason}")

                except json.JSONDecodeError:
                    pass

        except Exception as e:
            print(f"[SIA Core Error] {e}")

        time.sleep(5)

if __name__ == "__main__":
    monitor_drift()
