#!/usr/bin/env python3
"""
=============================================================================
SOVEREIGN ZERO-GAP MULTI-AGENT COUNCIL SPEECH STREAMER
Workspace: labs/workspaces/sovereign-agentic-app/core/audio
Mission: Eliminates the multi-second process launch gap between agent voices.
         Loads Kokoro ONNX model ONCE into memory, synthesizes all council
         utterances sequentially, concatenates with organic conversational
         cadence (250ms breath pause), and plays seamlessly.
=============================================================================
"""

import os
import sys
import json
import time
import numpy as np

try:
    import soundfile as sf
except ImportError:
    sf = None

from kokoro_onnx import Kokoro

APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODELS_DIR = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/capabilities/neural_models"
MODEL_PATH = os.path.join(MODELS_DIR, "kokoro-v1.0.onnx")
VOICES_PATH = os.path.join(MODELS_DIR, "voices.bin")

OUTPUT_WAV = "/tmp/council_unified_speech.wav"

VOICE_MAP = {
    "maxx": "am_adam",
    "clara": "af_bella",
    "vance": "am_michael",
    "daxx": "am_fenrir",
    "john": "am_eric",
    "eden": "af_sarah",
}

def stream_council_dialogue(utterances):
    """
    utterances: list of dicts [{"agent": "maxx", "text": "..."}]
    """
    if not os.path.exists(MODEL_PATH) or not os.path.exists(VOICES_PATH):
        print(f"[Error] Neural model missing at {MODELS_DIR}", file=sys.stderr)
        return False

    print(f"[+] Initializing Resident Kokoro Neural Engine (Single Memory Load)...")
    t0 = time.time()
    kokoro = Kokoro(MODEL_PATH, VOICES_PATH)
    print(f"[+] Neural Engine online in {time.time() - t0:.2f}s")

    combined_samples = []
    target_sample_rate = 24000

    # 250ms organic silence buffer between speakers
    pause_samples = np.zeros(int(target_sample_rate * 0.25), dtype=np.float32)

    for idx, item in enumerate(utterances):
        agent = item.get("agent", "maxx").lower()
        text = item.get("text", "").strip()
        if not text:
            continue

        voice_id = VOICE_MAP.get(agent, "am_adam")
        print(f"[*] Synthesizing [{agent.upper()}] with voice '{voice_id}'...")

        samples, sr = kokoro.create(text, voice=voice_id, speed=1.05, lang="en-us")
        target_sample_rate = sr

        # Soft 25ms fade-in/fade-out envelope to eliminate pops
        fade_len = min(int(sr * 0.025), len(samples) // 4)
        if fade_len > 0:
            fade_in = np.sin(np.linspace(0, np.pi / 2, fade_len)) ** 2
            fade_out = np.sin(np.linspace(np.pi / 2, 0, fade_len)) ** 2
            samples[:fade_len] *= fade_in
            samples[-fade_len:] *= fade_out

        if len(combined_samples) > 0:
            combined_samples.append(pause_samples)

        combined_samples.append(samples)

    if not combined_samples:
        print("[!] No speech samples generated.")
        return False

    final_audio = np.concatenate(combined_samples)
    print(f"[+] Total council speech duration: {len(final_audio) / target_sample_rate:.2f}s")

    if sf:
        sf.write(OUTPUT_WAV, final_audio, target_sample_rate)
    else:
        # Fallback raw write
        import wave
        with wave.open(OUTPUT_WAV, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(target_sample_rate)
            wf.writeframes((final_audio * 32767).astype(np.int16).tobytes())

    print("[+] Playing seamless council dialogue via afplay...")
    os.system(f"afplay '{OUTPUT_WAV}'")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Can pass json file or json string
        arg = sys.argv[1]
        if os.path.exists(arg):
            with open(arg, "r") as f:
                utterances = json.load(f)
        else:
            try:
                utterances = json.loads(arg)
            except Exception:
                # Fallback: agent and text as separate args
                utterances = [{"agent": sys.argv[1], "text": " ".join(sys.argv[2:])}]
        stream_council_dialogue(utterances)
    else:
        print("Usage: stream_council_speech.py '<json_array>'")
