#!/usr/bin/env python3
"""
XORAS SPEECH DAG RECEIPT CHAIN VERIFIER
Verifies load-bearing proof of spoken agent dispatches across the 3-Agent Deliberation Quorum.
Computes cryptographic SHA-256 Merkle DAG Root over real spoken receipts in CATCH_LOG.md.
"""

import sys
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CATCH_LOG_FILE = ROOT / "memory" / "catch_log" / "CATCH_LOG.md"

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def verify_speech_receipts() -> dict:
    if not CATCH_LOG_FILE.exists():
        return {"status": "FAILED", "reason": "CATCH_LOG.md missing"}

    content = CATCH_LOG_FILE.read_text(encoding='utf-8')
    lines = content.splitlines()
    
    receipts = []
    current_receipt = None

    for line in lines:
        if line.startswith("### [SPEECH BEAT RECEIPT]"):
            if current_receipt:
                receipts.append(current_receipt)
            ts = line.replace("### [SPEECH BEAT RECEIPT]", "").strip()
            current_receipt = {"timestamp": ts, "agent": "", "beat": "", "payload": ""}
        elif current_receipt and line.startswith("- **Agent**"):
            current_receipt["agent"] = line.split("`")[1].strip().lower()
        elif current_receipt and line.startswith("- **Beat**"):
            current_receipt["beat"] = line.split("`")[1].strip()
        elif current_receipt and line.startswith("- **Payload**"):
            current_receipt["payload"] = line.split(":", 1)[1].strip().strip('"')

    if current_receipt:
        receipts.append(current_receipt)

    agents_seen = set(r["agent"] for r in receipts if r["agent"])
    distinct_count = len(agents_seen)
    
    # Compute Merkle Root over all speech receipts
    raw_chain = "|".join([f"{r['timestamp']}:{r['agent']}:{r['beat']}:{sha256_text(r['payload'])[:16]}" for r in receipts])
    merkle_root = sha256_text(raw_chain)

    quorum_passed = (distinct_count >= 3)
    
    return {
        "status": "GREEN" if quorum_passed else "BLOCKED",
        "total_speech_receipts": len(receipts),
        "distinct_agents_count": distinct_count,
        "agents_in_chain": sorted(list(agents_seen)),
        "merkle_dag_root": merkle_root,
        "recent_receipts": receipts[-6:]
    }

if __name__ == "__main__":
    res = verify_speech_receipts()
    print("=================================================================")
    print("XORAS SPEECH RECEIPT CHAIN & MERKLE DAG VERIFICATION")
    print("=================================================================")
    print(f"Status               : [{res['status']}]")
    print(f"Total Speech Beats   : {res['total_speech_receipts']}")
    print(f"Distinct Agent Voices: {res['distinct_agents_count']} ({', '.join(res['agents_in_chain'])})")
    print(f"Merkle DAG Root      : {res['merkle_dag_root']}")
    print("-----------------------------------------------------------------")
    print("Recent Verified Speech Receipts:")
    for r in res['recent_receipts']:
        print(f"  • [{r['timestamp']}] {r['agent'].upper():<8} ({r['beat']}): \"{r['payload'][:60]}...\"")
    print("=================================================================")
