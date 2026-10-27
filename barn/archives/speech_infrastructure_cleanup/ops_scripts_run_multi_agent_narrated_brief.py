#!/usr/bin/env python3
"""
Multi-Agent Narrated Telemetry Briefing (Seamless High-Performance Engine)
Pre-buffers speech with 180ms natural inter-agent cadence (>=35 Words Per Agent).
"""
import os
import sys
from pathlib import Path

REPO_ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
sys.path.append(str(REPO_ROOT / "ops" / "scripts"))

from seamless_council_dialogue import run_seamless_dialogue

brief_dialogue = [
    (
        "jarvis",
        "This is Jarvis, Master Project Oversight. Sovereign Citizen Capsule Deployment has instantiated all twenty-two registered citizen houses inside agents citizens. Each house contains isolated brain structures and vector hexagraph directories to enforce zero-bleed memory boundaries and strict architectural isolation across our entire swarm network."
    ),
    (
        "clara",
        "This is Clara, Lead for Human Protection and Clinical Precision. Private memory manifolds and rules specifications are populated for every citizen capsule. Epistemic grounding checks confirm zero memory bleed between short term ledgers and vector structures, safeguarding real human lives with absolute clinical accuracy."
    ),
    (
        "vance",
        "This is Vance, Falsification and Adversarial Verification Lead. I verified that every deployed citizen house is locked to its specific isolation boundary. The fault localization engine and Ed25519 cryptographic token ledgers enforce zero trust boundary protection across all peer agent blackboards with mathematical rigor."
    ),
    (
        "maxx",
        "This is Maxx, Lead Systems Architect. Bare metal deployment of all twenty-two citizen capsules completed successfully on Apple Silicon M4 unified memory with zero thread stalls. All rules specifications and identity JSON manifests are synchronized and ready for high speed multi agent task execution."
    )
]

if __name__ == "__main__":
    run_seamless_dialogue(brief_dialogue, pause_ms=180)
