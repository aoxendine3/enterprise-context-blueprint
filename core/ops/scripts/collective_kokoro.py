#!/usr/bin/env python3
"""
Collective voice via Kokoro — the model is ours, the voice DAXX ('am_michael').
Input: single argument = text to speak. Exits non-zero on failure.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve()
while not (ROOT / ".git").exists() and ROOT != ROOT.parent:
    ROOT = ROOT.parent

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
        audio, sr = k.create(text, voice="am_michael", speed=1.0, lang="en-us")
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
