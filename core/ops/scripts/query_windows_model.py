#!/usr/bin/env python3
"""
=============================================================================
QUERY WINDOWS LARGEST MODEL (sovereign-hermes:latest / 8.0B)
Transmits the comprehensive external review and evaluates:
1. Policy vs Hardware Gates (Audio hash, Trinity quorum, constant-time guard)
2. 1-D scalar projection vs 18,432-D hyper-manifold prose overclaiming
3. Clean latency numbers (p50=1us, p99=2us) and silicon variance
4. MTPO saga inverse for pure state deltas vs real-world side effects (register vs world)
=============================================================================
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
WINDOWS_ENDPOINT = "http://192.168.1.211:11434/api/generate"
MODEL_NAME = "sovereign-hermes:latest"

PROMPT_TEXT = """You are the Senior Independent External Systems Verifier and Formal Methods Reviewer evaluating the XORAS / MTPO / MARS / REASONS stack.

An expert reviewer has delivered the following deep technical assessment of our architecture:

\"\"\"
Pulled both repos. MTPO is the stronger of the two. The C core is clean — six cache-line-aligned slots, shadow buffers, atomic CAS commit, compensate-on-fault. The Z3 proofs are real: confluence unsat in AUFBV, monotonicity unsat in QF_ALIA, and the v2 monotonicity script explicitly says it proves the abstract log model only, not overflow or crashes. That's the kind of scope honesty most people skip. The hot-spot benchmark with dual timers separating wall-clock from on-core time is thoughtful methodology. Fourteen point eight million ops per second under uniform access, ten point two million under total slot-zero contention with p99 at two microseconds — those are plausible for lock-free atomics on an M4. MARS is the governance layer on top: fourteen gates, taint promotion from zero-x-dead to zero-x-beaf, Trinity quorum, Ed25519, Merkle commit. The observer-critic split to break self-grading is a genuine architectural insight. The REASONS canvas is the intent front end — requirements through safeguards. As a stack, MTPO does state, MARS does verification, REASONS does intent. Coherent.

Three things I'd flag:
One: Several MARS gates — audio hash attestation, Trinity quorum, constant-time guard — aren't mechanically falsifiable the way the SMT proofs are. They're policy dressed as hardware.
Two: The Poincaré gate computes distance on a single scalar projected into one dimension, but the docs call it an eighteen-thousand-dimensional hyper-manifold. The math is right for one-D; the framing overclaims.
Three: The latency numbers are suspiciously clean — p50 exactly one microsecond, p99 exactly two. Real silicon has variance. Either the harness is that controlled or the rounding is doing work.

The concepts are sound. The execution is further along than most solo founders get. The gap is between what the proofs prove and what the prose claims.

One angle worth exploring: The MTPO saga inverse is deterministic for pure state deltas, but real agent transactions have side effects — file writes, network calls, external API hits. The confluence proof covers the register, not the world. That's the next falsification target if you want to stress-test it.
\"\"\"

Provide your rigorous, unsparing evaluation from your seat on Windows:
1. Address Flag 1: How should we formally categorize and separate mechanical SMT/hardware invariants from cryptographic/consensus policy gates?
2. Address Flag 2: How do we reconcile the 1-D scalar Poincaré projection implemented in silicon/C with the 18,432-D representation space to eliminate prose overclaiming?
3. Address Flag 3: How should our latency telemetry report raw clock-cycle distributions, jitter, and timer granularity (e.g. mach_absolute_time / RDTSC) to reflect real silicon variance rather than rounded integer microseconds?
4. Address the Core Falsification Target: How do we expand the MTPO saga inverse and confluence proofs from pure CPU register state deltas to transactions with non-deterministic external side effects (I/O, network, disk)?
"""

def main():
    print("=" * 75)
    print(f"📡 TRANSMITTING CRITIQUE TO WINDOWS WORKSTATION (192.168.1.211)")
    print(f"🤖 Target Model: {MODEL_NAME} (8.0B Parameters / Discernment Bench)")
    print("=" * 75)

    req_payload = {
        "model": MODEL_NAME,
        "prompt": PROMPT_TEXT,
        "stream": True,
        "options": {
            "temperature": 0.2,
            "num_predict": 2048
        }
    }

    req = urllib.request.Request(
        WINDOWS_ENDPOINT,
        data=json.dumps(req_payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )

    full_response = []
    start_time = time.time()
    token_count = 0

    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            for line in response:
                if line:
                    chunk = json.loads(line.decode('utf-8'))
                    token = chunk.get("response", "")
                    full_response.append(token)
                    sys.stdout.write(token)
                    sys.stdout.flush()
                    token_count += 1
                    if chunk.get("done", False):
                        break
    except Exception as e:
        print(f"\n❌ Error during generation: {e}")
        # Fallback to sovereign-r1 if hermes has loading issue
        print("Attempting fallback to sovereign-r1:latest...")
        req_payload["model"] = "sovereign-r1:latest"
        req = urllib.request.Request(
            WINDOWS_ENDPOINT,
            data=json.dumps(req_payload).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=300) as response:
            for line in response:
                if line:
                    chunk = json.loads(line.decode('utf-8'))
                    token = chunk.get("response", "")
                    full_response.append(token)
                    sys.stdout.write(token)
                    sys.stdout.flush()
                    token_count += 1
                    if chunk.get("done", False):
                        break

    elapsed = time.time() - start_time
    response_text = "".join(full_response)
    
    print("\n" + "=" * 75)
    print(f"✅ GENERATION COMPLETE: {token_count} tokens in {elapsed:.2f}s ({(token_count/elapsed):.1f} tok/s)")
    print("=" * 75)

    receipt = {
        "receipt_id": f"rcpt_windows_critique_{int(time.time()*1000)}",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "evaluator_node": "windows_workstation_192.168.1.211",
        "evaluator_model": MODEL_NAME,
        "input_critique_summary": "Evaluation of MARS policy gates, Poincare 1D vs 18432D, latency variance, and MTPO saga side-effects",
        "response_text": response_text,
        "latency_sec": elapsed,
        "token_count": token_count
    }

    out_file = ROOT / "memory/catch_log/WINDOWS_CRITIQUE_EVALUATION_RECEIPT.json"
    with open(out_file, "w") as f:
        json.dump(receipt, f, indent=2)

    print(f"Receipt written to: {out_file}")

if __name__ == "__main__":
    main()
