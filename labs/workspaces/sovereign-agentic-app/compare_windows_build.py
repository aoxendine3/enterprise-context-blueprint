#!/usr/bin/env python3
"""
=============================================================================
CROSS-NODE ARCHITECTURE & BUILD COMPARISON
Queries sovereign-hermes:latest on Windows (192.168.1.211) via streaming
to analyze the present Windows build state vs macOS M4 SSOT Monorepo.
=============================================================================
"""

import os
import sys
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
APP_DIR = ROOT / "labs/workspaces/sovereign-agentic-app"
WINDOWS_ENDPOINT = "http://192.168.1.211:11434/api/generate"
MODEL_NAME = "sovereign-hermes:latest"

PROMPT_TEXT = """You are the Senior Systems Architect on the Windows x86_64 Node (192.168.1.211).

Compare and analyze the present build on the Windows node versus the SSOT Monorepo build on the Apple Silicon M4 node:

1. Present Windows Build Posture:
   - Hardware: x86_64 CPU workstation.
   - Memory Protection: Win32 VirtualAlloc / VirtualProtect (PAGE_READONLY, STATUS_ACCESS_VIOLATION 0xC0000005).
   - Core Binaries: truth_verifier_v4_cli.exe, libtruth_verifier.dll.
   - Inference: Ollama local cluster (sovereign-hermes 8B, sovereign-r1 1.8B).
   - Role: Independent adversarial witness, second-opinion verification, external critic.

2. Present SSOT Monorepo Build on macOS M4:
   - Hardware: Apple Silicon M4 (ARM64 NEON, unified memory).
   - Memory Protection: Darwin XNU mprotect (PROT_READ, SIGBUS/SIGSEGV).
   - Core Engines: MTPO lock-free C core (14.8M ops/sec), 18,432-D Poincare Mobius Gyrovector SIMD Rust engine (84us), Merkle DAG lineage engine, and sovereign-agentic-app policy.sovra.
   - Role: Primary state engine, rapid low-latency local execution, canonical Merkle root authority.

Provide your structured comparative evaluation:
A. What are the key architectural differences and substrate divergence between the two builds?
B. What security and verification guarantees are identical across both machines?
C. Where do we stand in parity, and what are the top 3 concrete action items to achieve 100% cross-platform parity?

Be concise, technical, and objective.
"""

def main():
    print("=" * 70)
    print("📡 STREAMING BUILD COMPARISON QUERY TO WINDOWS (192.168.1.211)")
    print("=" * 70)

    req_payload = {
        "model": MODEL_NAME,
        "prompt": PROMPT_TEXT,
        "stream": True,
        "options": {
            "temperature": 0.2,
            "num_predict": 400
        }
    }

    req = urllib.request.Request(
        WINDOWS_ENDPOINT,
        data=json.dumps(req_payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )

    full_tokens = []
    start_time = time.time()
    token_count = 0

    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            for line in response:
                if line:
                    chunk = json.loads(line.decode('utf-8'))
                    token = chunk.get("response", "")
                    full_tokens.append(token)
                    sys.stdout.write(token)
                    sys.stdout.flush()
                    token_count += 1
                    if chunk.get("done", False):
                        break
    except Exception as e:
        print(f"\n❌ Error during generation: {e}")
        return False

    elapsed = time.time() - start_time
    response_text = "".join(full_tokens)

    print("\n" + "=" * 70)
    print(f"✅ COMPARISON COMPLETE: {token_count} tokens in {elapsed:.2f}s")
    print("=" * 70)

    receipt = {
        "audit_id": "audit_windows_vs_m4_build_comparison",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "evaluator_node": "windows_workstation_192.168.1.211",
        "evaluator_model": MODEL_NAME,
        "comparison_report": response_text,
        "elapsed_seconds": elapsed,
        "tokens_generated": token_count
    }

    receipt_file = APP_DIR / "audit_windows_build_comparison_receipt.json"
    with open(receipt_file, "w") as f:
        json.dump(receipt, f, indent=2)

    print(f"Report saved to: {receipt_file}")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
