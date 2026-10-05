#!/usr/bin/env python3
import os, sys, time, json, subprocess

SSOT_ROOT = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain"
LOG_PATH = os.path.join(SSOT_ROOT, "memory/agent_logs/sentinel_heartbeat.jsonl")

print("=== SOVEREIGN 24/7 SENTINEL DAEMON INITIALIZED ===")

def check_system_integrity():
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    # 1. Check Manifest Integrity
    manifest_file = os.path.join(SSOT_ROOT, "identity/sovereign_citizens_manifest.json")
    manifest_ok = os.path.exists(manifest_file)
    
    # 2. Check Out-of-Band Witness Integrity
    witness_file = os.path.expanduser("~/.sovereign_witness/out_of_band_merkle_witness.jsonl")
    witness_ok = os.path.exists(witness_file)
    
    # 3. Check Canonical Audio Script Permissions
    speak_script = os.path.join(SSOT_ROOT, "ops/scripts/agent_speak.sh")
    audio_ok = os.path.exists(speak_script) and os.access(speak_script, os.X_OK)
    
    status_entry = {
        "timestamp": timestamp,
        "manifest_ok": manifest_ok,
        "witness_ok": witness_ok,
        "audio_ok": audio_ok,
        "status": "HEALTHY" if (manifest_ok and witness_ok and audio_ok) else "ANOMALY_DETECTED"
    }
    
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(status_entry) + "\n")
        
    print(f"[{timestamp}] Sentinel Heartbeat Logged: Status={status_entry['status']}")

if __name__ == "__main__":
    check_system_integrity()
