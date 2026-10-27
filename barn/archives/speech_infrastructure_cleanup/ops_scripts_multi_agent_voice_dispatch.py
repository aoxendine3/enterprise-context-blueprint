#!/usr/bin/env python3
"""
ORION MEDIA DIRECTOR CANONICAL CAPSULE VOICE DISPATCHER
Reads directly from Xoras_agent_cards/<agent_id>.json for exact card voice alignment.
"""

import sys
import os
import json
import subprocess
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
CARDS_DIR = ROOT / "Xoras_agent_cards"

def speak_via_orion(agent_id: str, speech_text: str):
    agent_key = agent_id.lower().strip()
    card_json = CARDS_DIR / f"{agent_key}.json"
    card_md = CARDS_DIR / f"{agent_key}.md"
    
    if not card_json.is_file():
        print(f"❌ ORION GATEWAY REJECTED: No canonical capsule card found for '{agent_id}' at {card_json}")
        sys.exit(1)
        
    with open(card_json, "r", encoding="utf-8") as f:
        card = json.load(f)
        
    kokoro_id = card.get("kokoro_voice_id", "bm_lewis")
    mac_voice_raw = card.get("mac_fallback_voice", "Daniel")
    
    # Strip parenthetical annotations for macOS 'say' (e.g. "Tom (Enhanced)" -> "Tom")
    clean_mac_voice = mac_voice_raw.split("(")[0].strip()
    
    agent_name = card.get("name", agent_id.capitalize())
    role = card.get("role", "Sovereign Citizen")
    seat = card.get("seat", "N/A")
    
    print("================================================================================")
    print(f"🎬 [ORION MEDIA DIRECTOR CAPSULE DISPATCH]")
    print(f"   Agent Name : {agent_name} (Seat {seat})")
    print(f"   Agent Role : {role}")
    print(f"   Kokoro Voice: {kokoro_id}")
    print(f"   macOS Voice : {clean_mac_voice} (Raw Card Setting: {mac_voice_raw})")
    print(f"   Speech Text : \"{speech_text}\"")
    print("================================================================================")
    
    # Orion Media Director stage dispatch call
    dispatch_payload = f"Orion stage dispatch for {agent_name}: {speech_text}"
    cmd = ["say", "-v", clean_mac_voice, dispatch_payload]
    subprocess.run(cmd)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: multi_agent_voice_dispatch.py <agent_id> <speech_text>")
        sys.exit(1)
        
    target_agent = sys.argv[1]
    text_payload = " ".join(sys.argv[2:])
    speak_via_orion(target_agent, text_payload)
