#!/usr/bin/env python3
"""
=============================================================================
XORAS_OS: LOCAL CODER (7B) REVIEW & DISPENSATION ENGINE
Architecture: Apple Silicon M4 Unified Memory Architecture
Model: qwen2.5-coder:7b (Local Ollama Engine, 0 Cloud Tokens)
Governance: Log Entry #066 & #067
=============================================================================
"""

import os, sys, json, urllib.request, subprocess, time

PROMOTER_SCRIPT = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/discernment/ring_promoter.py"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

def audit_and_dispense(artifact_path, target_rel_path, asset_id, description):
    print("=================================================================")
    print(f"🤖 LOCAL 7B CODER AUDIT & PROMOTION: {asset_id}")
    print("=================================================================")
    
    if not os.path.exists(artifact_path):
        print(f"[-] Artifact does not exist: {artifact_path}", file=sys.stderr)
        return False
        
    with open(artifact_path, "r", errors="ignore") as f:
        code_snippet = f.read(4000) # Read initial bytes for local 7B evaluation
        
    prompt = f"""You are Vance's deterministic security sentinel on Apple Silicon M4.
Evaluate this artifact for zero-cloud sovereignty, memory safety, and structural soundness.
Artifact: {asset_id}
Code:
```
{code_snippet}
```
If clean and sovereign, reply starting with 'VERIFIED: ' followed by a 2-sentence rationale. Otherwise reply 'REJECTED'."""

    print("[1/3] Querying local qwen2.5-coder:7b on metal (0 cloud tokens)...")
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps({
            "model": "qwen2.5-coder:7b",
            "prompt": prompt,
            "stream": False
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res = json.loads(response.read().decode())
            review_text = res.get("response", "").strip()
            print(f"[2/3] Local 7B Model Verdict:\n{review_text}")
    except Exception as e:
        print(f"[-] Local model evaluation failed: {e}", file=sys.stderr)
        return False
        
    if "VERIFIED" not in review_text.upper():
        print(f"[-] Review rejected by local 7B sentinel: {review_text}", file=sys.stderr)
        return False
        
    print("[3/3] Passing to Ring Promoter with Cryptographic Handshake...")
    res = subprocess.run([
        "python3", PROMOTER_SCRIPT,
        artifact_path, target_rel_path, asset_id, description
    ])
    return res.returncode == 0

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: local_coder_review_daemon.py <artifact_path> <target_rel_path> <asset_id> <description>")
        sys.exit(1)
    ok = audit_and_dispense(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    sys.exit(0 if ok else 1)
