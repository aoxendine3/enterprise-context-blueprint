#!/usr/bin/env python3
"""
=============================================================================
TRINITY GATE (v2.0 - UNCOMPROMISED BFT AUDIO QUORUM GATE)
Governance: Log Entry #066 & Log Entry #078
Substrate: Apple Silicon M4 Bare Metal
=============================================================================
Rules:
  1. No padding, no duplicating hashes, no 'dummyhash'.
  2. Verifies physical existence and SHA-256 integrity of audio briefings on disk.
  3. Enforces strict 2-out-of-3 distinct agent approval (Maxx, Clara, Vance).
  4. Fails closed if <2 distinct valid votes exist.
=============================================================================
"""

import os
import sys
import json
import hashlib
from datetime import datetime, timezone

WORKSPACE_ROOT = os.path.expanduser("~/Desktop/SSOT_Agentic_Brain")
HASHES_PATH = os.path.join(WORKSPACE_ROOT, "memory", "tri_brain", "trinity_hashes.jsonl")
GATE_LOG = os.path.join(WORKSPACE_ROOT, "memory", "catch_log", "trinity_gate.log")

REQUIRED_AGENTS = {"MAXX", "CLARA", "VANCE"}
EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

def verify_trinity_quorum():
    if not os.path.exists(HASHES_PATH):
        print(json.dumps({"error": "trinity_hashes.jsonl missing", "passed": False}))
        sys.exit(1)

    records = []
    with open(HASHES_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    records.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue

    approved_agents = set()
    verified_hashes = set()
    errors = []

    for r in records:
        agent = r.get("agent")
        claimed_hash = r.get("hash", "")
        rel_path = r.get("audio_file", "")
        status = r.get("status", "")

        if agent not in REQUIRED_AGENTS:
            continue

        if not claimed_hash or claimed_hash == EMPTY_SHA256:
            errors.append(f"{agent}: Empty or invalid hash")
            continue

        # Check cyclic rotation of empty hash
        is_rot = len(claimed_hash) == 64 and any(claimed_hash == (EMPTY_SHA256[k:] + EMPTY_SHA256[:k]) for k in range(64))
        if is_rot:
            errors.append(f"{agent}: Cyclic rotation of empty hash detected")
            continue

        # Physical file verification
        full_audio_path = os.path.join(WORKSPACE_ROOT, rel_path)
        if not os.path.exists(full_audio_path):
            errors.append(f"{agent}: Audio file missing on disk: {rel_path}")
            continue

        file_sz = os.path.getsize(full_audio_path)
        if file_sz < 10000: # Audio must be substantial (>10KB)
            errors.append(f"{agent}: Audio file suspiciously small: {file_sz} bytes")
            continue

        with open(full_audio_path, "rb") as f:
            disk_hash = hashlib.sha256(f.read()).hexdigest()

        if disk_hash != claimed_hash:
            errors.append(f"{agent}: Hash mismatch: claimed {claimed_hash[:8]} != disk {disk_hash[:8]}")
            continue

        if status == "APPROVED":
            approved_agents.add(agent)
            verified_hashes.add(disk_hash)

    passed = len(approved_agents) >= 2 and len(verified_hashes) >= 2

    # Log receipt
    os.makedirs(os.path.dirname(GATE_LOG), exist_ok=True)
    log_entry = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "approved_agents": list(approved_agents),
        "verified_hashes": list(verified_hashes),
        "errors": errors,
        "quorum_passed": passed
    }
    with open(GATE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

    output = {
        "gate": "TRINITY_QUORUM_BFT",
        "passed": passed,
        "approved_count": len(approved_agents),
        "threshold": 2,
        "agents": list(approved_agents),
        "hashes": list(verified_hashes),
        "errors": errors
    }

    print(json.dumps(output))
    sys.exit(0 if passed else 1)

if __name__ == "__main__":
    verify_trinity_quorum()
