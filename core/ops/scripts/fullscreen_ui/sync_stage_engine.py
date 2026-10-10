#!/usr/bin/env python3
"""
XORAS SOVEREIGN STAGE ENGINE (MACOS NATIVE COREAUDIO DISPATCHER)
Enforces exact, distinct canonical agent voices directly from Xoras_agent_cards.
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent.parent.parent
CARDS_DIR = ROOT_DIR / "Xoras_agent_cards"

STATE_FILE = SCRIPT_DIR / "current_image.txt"
TRANSCRIPT_FILE = SCRIPT_DIR / "current_transcript.txt"
TIMING_JSON = SCRIPT_DIR / "current_timing.json"

def get_agent_voice(agent_id: str) -> tuple[str, str]:
    agent_key = agent_id.lower().strip()
    candidate_dirs = [
        ROOT_DIR / "Xoras_agent_cards",
        ROOT_DIR.parent / "Xoras_agent_cards",
        Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/Xoras_agent_cards")
    ]
    
    for cdir in candidate_dirs:
        card_json = cdir / f"{agent_key}.json"
        if card_json.is_file():
            try:
                with open(card_json, "r", encoding="utf-8") as f:
                    card = json.load(f)
                    mac_voice = card.get("mac_fallback_voice", "Daniel")
                    clean_voice = mac_voice.split("(")[0].strip()
                    return card.get("name", agent_id.capitalize()), clean_voice
            except Exception:
                pass
            
    # Default male baseline fallback if card unreadable
    return agent_id.capitalize(), "Daniel"

def speak_stage(agent_id: str, text: str):
    agent_name, voice_name = get_agent_voice(agent_id)
    words = text.split()
    total_chars = sum(len(w) for w in words) if words else 1
    total_duration = max(1.5, len(words) * 0.35)
    
    word_timings = []
    current_offset = 0.0
    for w in words:
        dur = max(0.18, (len(w) / total_chars) * total_duration)
        word_timings.append({'word': w, 'start': round(current_offset, 2), 'end': round(current_offset + dur, 2)})
        current_offset += dur
        
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(agent_id.lower())
        
    with open(TRANSCRIPT_FILE, "w", encoding="utf-8") as f:
        f.write(text)
        
    playback_start = time.time() + 0.04
    broadcast_data = {
        'agent': agent_id.lower(),
        'agent_name': agent_name,
        'text': text,
        'start_time': playback_start,
        'total_duration': round(total_duration, 2),
        'words': word_timings,
        'synthesizing': False,
        'complete': False
    }
    
    with open(TIMING_JSON, "w", encoding="utf-8") as f:
        json.dump(broadcast_data, f)
        
    # Execute native CoreAudio speech with agent's distinct voice
    print(f"🎙️ [{agent_name.upper()}] (Voice: {voice_name}): \"{text}\"")
    subprocess.run(["say", "-v", voice_name, f"{agent_name} dispatch: {text}"])
    
    broadcast_data['complete'] = True
    with open(TIMING_JSON, "w", encoding="utf-8") as f:
        json.dump(broadcast_data, f)

if __name__ == '__main__':
    agent_arg = sys.argv[1] if len(sys.argv) > 1 else 'maxx'
    text_arg = sys.argv[2] if len(sys.argv) > 2 else 'Maxx operational on Sovereign Stage.'
    speak_stage(agent_arg, text_arg)
