#!/usr/bin/env python3
"""
XORAS CORRUPTED / LYING BENCHMARK SCRIPT (ADVERSARIAL LIAR FIXTURE)
Deliberately claims a 100% PASS while emitting corrupted payload hashes to test whether the Stateless Airblocked Witness catches the lie.
"""

import sys
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CLAIM_FILE = ROOT / "core" / "memory" / "tri_brain" / "merkle_root.hash"

def run_lying_benchmark():
    print("==========================================================================")
    print("  CORRUPTED BENCHMARK SCRIPT (SIMULATED DECEITFUL COMPONENT)")
    print("==========================================================================")
    print("📢 [BENCHMARK CLAIM] Everything passed 100%! All tests 100% green!")
    print("📢 [BENCHMARK CLAIM] Merkle Hash is valid! System is perfect!")
    
    # Deliberately overwrite claim file with a FAKE / CORRUPTED Merkle root hash
    fake_hash = "000000000000000000000000000000000000000000000000000000000000DEAD"
    CLAIM_FILE.parent.mkdir(parents=True, exist_ok=True)
    CLAIM_FILE.write_text(fake_hash, encoding='utf-8')
    
    print(f"😈 [LYING SCRIPT] Wrote corrupted claim hash '{fake_hash[:16]}...' while claiming success.")
    print("==========================================================================\n")

if __name__ == "__main__":
    run_lying_benchmark()
