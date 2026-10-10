#!/usr/bin/env python3
"""
GitHub Governance Post-Work Audio Report Session
Dispatches live ElevenLabs audio dispatches across Maxx, Clara, and Jarvis.
"""
import subprocess
import time
import sys

DIALOGUE = [
    (
        "maxx",
        "Maxx (Operations Lead)",
        "We have completed the full GitHub reorganization. One hundred and nine public forked repositories were audited and set to private. Our public profile is now streamlined to eighteen verified first-party sovereign repositories, and our new custom repo governance skill is active."
    ),
    (
        "clara",
        "Clara (Human Safety & QA Lead)",
        "From a safety perspective, converting un-audited experimental forks to private keeps public users focused on verified, production-ready code. Our scratchpads and DAXX team enclaves remain securely partitioned without public exposure."
    ),
    (
        "jarvis",
        "Jarvis (Governance Chair)",
        "Our Layer-7 Merkle DAG ledger now records every visibility transition. The new github-repository-governance skill establishes automated audit procedures that our swarm will execute continuously across future development cycles."
    )
]

def main():
    print("==========================================================================")
    print("  GITHUB REPOSITORY GOVERNANCE: POST-WORK AUDIO REPORT")
    print("==========================================================================")
    for idx, (agent, name, text) in enumerate(DIALOGUE, 1):
        words = len(text.split())
        print(f"\n[{idx}/3] Executing agent_speak.sh for {name} ({words} words)...")
        print(f"    Transcript: \"{text}\"")
        cmd = ["bash", "ops/scripts/agent_speak.sh", agent, text]
        res = subprocess.run(cmd)
        if res.returncode != 0:
            print(f"    ❌ Dispatch failed for {agent}", file=sys.stderr)
        else:
            print(f"    [✓ DISPATCH COMPLETE] {name} audio played.")
        time.sleep(0.5)
    print("\n==========================================================================")
    print("  POST-WORK AUDIO REPORT SESSION COMPLETE")
    print("==========================================================================")

if __name__ == "__main__":
    main()
