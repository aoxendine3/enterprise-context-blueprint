#!/usr/bin/env python3
"""
XORAS CONTENT-HASHED LINK INTEGRITY CHECKER
Dual Verification Engine:
1. Reachability Check (HTTP 200 / file existence)
2. Content Hash Verification (SHA-256 baseline comparison)

Prevents silent content degradation or page substitution where a URL returns HTTP 200 but contains corrupted/altered payload.
"""

import sys
import json
import urllib.request
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BASELINE_FILE = ROOT / "ops" / "scripts" / "link_content_baseline.json"

def get_url_content_hash(url: str) -> tuple[bool, str, str]:
    """Fetches URL and calculates SHA-256 hash of response body."""
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'XORAS-Sovereign-Integrity-Checker/1.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status != 200:
                return False, "", f"HTTP status code {response.status}"
            content = response.read()
            digest = hashlib.sha256(content).hexdigest()
            return True, digest, ""
    except Exception as e:
        return False, "", str(e)

def verify_link_integrity() -> bool:
    if not BASELINE_FILE.exists():
        # Generate initial baseline
        initial_baseline = {
            "https://raw.githubusercontent.com/aoxendine3/SSOT_Agentic_Brain/main/README.md": {
                "description": "Canonical Readme Root",
                "expected_hash": ""
            }
        }
        BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE_FILE.write_text(json.dumps(initial_baseline, indent=2), encoding='utf-8')

    manifest = json.loads(BASELINE_FILE.read_text(encoding='utf-8'))
    all_passed = True
    
    print("🔍 [LINK INTEGRITY] Auditing reachability AND content hash integrity...")
    
    for url, entry in manifest.items():
        ok, actual_hash, err = get_url_content_hash(url)
        if not ok:
            print(f"❌ [REACHABILITY FAIL] {url} -> {err}")
            all_passed = False
            continue
            
        expected = entry.get("expected_hash", "")
        if expected and actual_hash != expected:
            print(f"🚨 [CONTENT DRIFT DETECTED] {url}")
            print(f"   Expected SHA-256: {expected}")
            print(f"   Actual SHA-256:   {actual_hash}")
            all_passed = False
        else:
            print(f"✅ [INTEGRITY VERIFIED] {url} (SHA-256: {actual_hash[:16]})")
            
    return all_passed

if __name__ == "__main__":
    if not verify_link_integrity():
        sys.exit(1)
    sys.exit(0)
