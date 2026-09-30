#!/usr/bin/env python3
"""Minimal Agentic console app.

- No background pipeline (kept optional, removed for simplicity).
- REPL reads a line and forwards it to the Python sync script.
- No web UI is launched.
- Clean exit on Ctrl‑D.
"""
import subprocess
import sys

SYNC_SCRIPT = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/sync_stage_engine_kokoro.py"
PYTHON_BIN = "/opt/homebrew/bin/python3"

def speak(text: str, agent: str = "jarvis"):
    """Invoke the sync_stage_engine Python script which performs audio synthesis.
    """
    subprocess.run([PYTHON_BIN, SYNC_SCRIPT, agent, text], check=False)

print("Enter text to speak (Ctrl‑D to exit):")
try:
    while True:
        line = input("> ").strip()
        if line:
            speak(line)
except EOFError:
    pass

print("[Agentic] Session ended.")
