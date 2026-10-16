#!/usr/bin/env python3
"""
=============================================================================
SOVEREIGN AGENTIC APP: NATIVE RESIDENT AUDIO SPEECH ENGINE
Workspace: labs/workspaces/sovereign-agentic-app/ops/audio
Substrate: Apple Silicon M4 Neural Engine (Kokoro ONNX)
Anchored: 100% inside Sovereign Agentic App. Zero external reach.
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
MODELS_DIR = os.path.join(APP_ROOT, "capabilities", "neural_models")
MODEL_PATH = os.path.join(MODELS_DIR, "kokoro-v1.0.onnx")
VOICES_PATH = os.path.join(MODELS_DIR, "voices.bin")

OUTPUT_WAV = os.path.join(APP_ROOT, "ops", "audio", "council_speech.wav")

VOICE_MAP = {
    "maxx": "am_adam",
    "clara": "af_bella",
    "vance": "am_michael",
    "daxx": "am_fenrir",
    "john": "am_eric",
    "eden": "af_sarah",
}

_KOKORO_INSTANCE = None

def get_engine():
    global _KOKORO_INSTANCE
    if _KOKORO_INSTANCE is None:
        if not os.path.exists(MODEL_PATH) or not os.path.exists(VOICES_PATH):
            raise FileNotFoundError(f"Kokoro model missing inside Sovereign Agentic App at {MODELS_DIR}")
        _KOKORO_INSTANCE = Kokoro(MODEL_PATH, VOICES_PATH)
    return _KOKORO_INSTANCE

def speak_utterances(utterance_list):
    """
    utterance_list: list of dicts [{"agent": "maxx", "text": "..."}]
    """
    engine = get_engine()
    combined_samples = []
    target_sample_rate = 24000
    pause_samples = np.zeros(int(target_sample_rate * 0.25), dtype=np.float32)

    for item in utterance_list:
        agent = item.get("agent", "maxx").lower()
        text = item.get("text", "").strip()
        if not text:
            continue

        voice_id = VOICE_MAP.get(agent, "am_adam")
        samples, sr = engine.create(text, voice=voice_id, speed=1.05, lang="en-us")
        target_sample_rate = sr

        # Apply soft acoustic envelope (25ms cosine fade)
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
        return False

    final_audio = np.concatenate(combined_samples)
    if sf:
        sf.write(OUTPUT_WAV, final_audio, target_sample_rate)
    else:
        import wave
        with wave.open(OUTPUT_WAV, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(target_sample_rate)
            wf.writeframes((final_audio * 32767).astype(np.int16).tobytes())

    os.system(f"afplay '{OUTPUT_WAV}'")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: speak.py '<json_or_agent>' [text...]")
        sys.exit(1)

    arg = sys.argv[1]
    if arg.startswith("[") or os.path.exists(arg):
        if os.path.exists(arg):
            with open(arg, "r") as f:
                utterances = json.load(f)
        else:
            utterances = json.loads(arg)
    else:
        agent = sys.argv[1]
        text = " ".join(sys.argv[2:])
        utterances = [{"agent": agent, "text": text}]

    speak_utterances(utterances)
