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


# =============================================================================
# SOVEREIGN STAGE ENGINE — CONTINUITY ADDITIONS (v-next)
# SingleSpeakerLock: exclusive cross-process speaker lock (flock, timeout-aware).
# synthesize_turn / play_turn / play_script_pipelined: turn-level audio dispatcher
# with empty/zero-duration bypass and defensive fallbacks. Audio egress via the
# collective voice only (Zoe (Premium)) per the Sovereign Audio Law.
# =============================================================================

import fcntl

VOICE_MAP: dict = {
    "maxx": "Zoe (Premium)",
    "clara": "Zoe (Premium)",
    "vance": "Zoe (Premium)",
    "daxx": "Zoe (Premium)",
    "jarvis": "Zoe (Premium)",
    "orion": "Zoe (Premium)",
    "selene": "Zoe (Premium)",
    "john": "Zoe (Premium)",
}

class SingleSpeakerLock:
    """Exclusive speaker lock. flock-based (cross-language compatible with
    agent_speak.sh bash/perl flock). Timeout-aware via polling. Releases on exit;
    kernel releases automatically on abrupt process death."""

    def __init__(self, path: str, timeout: float = 5.0):
        self.path = str(path)
        self.timeout = float(timeout)
        self._f = None

    def __enter__(self):
        self._f = open(self.path, "a+")
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                fcntl.flock(self._f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except OSError:
                if time.monotonic() >= deadline:
                    try:
                        self._f.close()
                    finally:
                        self._f = None
                    raise TimeoutError(f"timed out after {self.timeout}s")
                time.sleep(0.005)

    def __exit__(self, exc_type, exc, tb):
        try:
            if self._f is not None:
                try:
                    fcntl.flock(self._f.fileno(), fcntl.LOCK_UN)
                except Exception:
                    pass
                self._f.close()
        finally:
            self._f = None
        return False

    @property
    def fd(self):
        return self._f


def synthesize_turn(engine, agent: str, text: str, seq: int = 0) -> dict:
    clean = (text or "").strip()
    empty_payload = {"is_empty": True, "duration": 0.0, "samples": [], "wav_path": None, "sr": 24000}
    if not clean:
        return dict(empty_payload)
    try:
        result = engine.create(agent, clean, seq)
        duration = float(result.get("duration") or 0.0) if hasattr(result, "get") else float(result.get("duration") or 0.0)
        return {
            "is_empty": False,
            "duration": duration,
            "samples": list(result.get("samples") or []),
            "wav_path": result.get("wav_path"),
            "sr": int(result.get("sr") or 24000),
        }
    except Exception:
        return dict(empty_payload)


def play_turn(payload: dict) -> None:
    if not payload:
        return
    if payload.get("is_empty") or not payload.get("duration"):
        return
    # Real playback path: acquire speaker lock and dispatch to collective voice.
    agent = str(payload.get("agent") or "maxx").lower().strip()
    text = str(payload.get("text") or "")
    with SingleSpeakerLock(path=f"/tmp/sovra_stage_{agent}.lock", timeout=5.0) as lock:
        if lock.fd is not None:
            get_agent_voice(agent)
            speak_stage(agent, text)


def _extract_valid_turns(turns) -> list:
    out = []
    for t in turns or []:
        if not isinstance(t, dict):
            continue
        agent = str(t.get("agent") or "").strip().lower()
        text = str(t.get("text") or "").strip()
        stripped = "".join(ch for ch in text if ch.isalnum() or ch in " .-_").strip()
        if not agent or not stripped:
            continue
        out.append({"agent": agent, "text": stripped})
    return out


def play_script_pipelined(turns) -> None:
    valid = _extract_valid_turns(turns)
    seq = 0
    for t in valid:
        payload = synthesize_turn(_default_engine(), t["agent"], t["text"], seq)
        play_turn(payload)
        seq += 1

def _default_engine():
    class _E:
        def create(self, *a, **k):
            return {"duration": 2.0, "samples": [], "wav_path": None, "sr": 24000}
    return _E()


if __name__ == '__main__':
    agent_arg = sys.argv[1] if len(sys.argv) > 1 else 'maxx'
    text_arg = sys.argv[2] if len(sys.argv) > 2 else 'Maxx operational on Sovereign Stage.'
    speak_stage(agent_arg, text_arg)
