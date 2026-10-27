#!/usr/bin/env python3
"""
XORAS CANONICAL AGENT SPEECH RUNTIME CONTRACT (4-BEAT BINDING LAW)
100% Mandatory runtime speech execution across all 4 lifecycle beats:
  1. INTENT     : Spoken out loud BEFORE executing any file edit, tool, or build script.
  2. STATUS     : Spoken out loud DURING active long-running work.
  3. RESULT     : Spoken out loud AFTER work finishes with verified output.
  4. TRANSITION : Spoken out loud BEFORE handing off to the next agent or task.

Zero silent executions. Zero clipboard scripts. Distinct vocal identity per agent seat.
"""

import sys
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SPEAK_SCRIPT = ROOT / "ops" / "scripts" / "agent_speak.sh"

VOICE_MAP = {
    "maxx": {"voice": "Evan (Enhanced)", "role": "Operations & Systems Lead"},
    "jarvis": {"voice": "Jamie (Premium)", "role": "Governance & Oversight Lead"},
    "daxx": {"voice": "Rocko (English (US))", "role": "Remediation & Debugging Master"},
    "clara": {"voice": "Zoe (Premium)", "role": "Physics & Mathematical Validation Lead"},
    "vance": {"voice": "Nathan (Enhanced)", "role": "Security & Blackbox Auditor"},
    "john": {"voice": "Daniel (Enhanced)", "role": "Infrastructure & Platform Lead"},
    "selene": {"voice": "Samantha", "role": "Data Sovereignty & Memory Lead"},
    "orion": {"voice": "Alex", "role": "Media Director & Stage Synthesizer"},
    "eden": {"voice": "Ava (Enhanced)", "role": "Product Strategy & Next Horizon Lead"}
}

def speak_beat(agent_id: str, beat_type: str, message: str) -> None:
    agent_clean = agent_id.lower().strip()
    beat_clean = beat_type.upper().strip()
    
    if beat_clean not in ["INTENT", "STATUS", "RESULT", "TRANSITION"]:
        beat_clean = "STATUS"
        
    prefix = f"[{beat_clean}]"
    full_speech = f"{message}"
    
    print(f"🔊 {prefix} [{agent_clean.upper()}]: {full_speech}")
    
    if SPEAK_SCRIPT.exists():
        try:
            subprocess.run(["bash", str(SPEAK_SCRIPT), agent_clean, full_speech], check=True, timeout=30)
        except Exception as e:
            print(f"[WARN] Audio speak failed for {agent_clean}: {e}", file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) >= 4:
        speak_beat(sys.argv[1], sys.argv[2], " ".join(sys.argv[3:]))
    else:
        print("Usage: agent_speech_contract.py <agent_id> <INTENT|STATUS|RESULT|TRANSITION> <message>")
