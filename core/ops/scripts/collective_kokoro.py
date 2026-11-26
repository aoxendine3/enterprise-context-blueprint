#!/usr/bin/env python3
"""
Collective voice via Kokoro — the model is ours, the voice is Maxx's ('bm_george').
Team reports are spoken in the voice pinned on Maxx's sealed citizen card.
Input: single argument = text to speak. Exits non-zero on failure.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve()
while not (ROOT / ".git").exists() and ROOT != ROOT.parent:
    ROOT = ROOT.parent

REPORT_VOICE_FALLBACK = "bm_george"  # Maxx's original voice (card, 2026-09-30)


def report_voice() -> str:
    """Team reports are spoken in Maxx's voice, read from his sealed citizen card.

    The card is hash-pinned by identity_scope_guard, so the voice cannot drift
    silently. If the card is unreadable we fall back to the original voice
    rather than to any other agent's.
    """
    try:
        card = json.loads((ROOT / "Xoras_agent_cards" / "maxx.json").read_text(encoding="utf-8"))
        return card.get("kokoro_voice_id") or REPORT_VOICE_FALLBACK
    except Exception:
        return REPORT_VOICE_FALLBACK


def main():
    text = sys.argv[1] if len(sys.argv) > 1 else ""
    if not text.strip():
        return 2
    try:
        from kokoro_onnx import Kokoro
        import soundfile as sf
    except Exception as e:
        print(f"kokoro unavailable: {e}", file=sys.stderr)
        return 3
    try:
        k = Kokoro(str(ROOT / "capabilities" / "neural_models" / "kokoro-v1.0.onnx"),
                   str(ROOT / "capabilities" / "neural_models" / "voices.bin"))
        audio, sr = k.create(text, voice=report_voice(), speed=1.0, lang="en-us")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fh:
            sf.write(fh.name, audio, sr)
            wav_path = fh.name
        try:
            subprocess.run(["afplay", wav_path], check=True)
        finally:
            os.unlink(wav_path)
        return 0
    except Exception as e:
        print(f"kokoro failed: {e}", file=sys.stderr)
        return 4

if __name__ == "__main__":
    sys.exit(main())
