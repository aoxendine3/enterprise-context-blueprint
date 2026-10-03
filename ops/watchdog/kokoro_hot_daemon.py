import os
import sys
import json
import time

SCRIPT_DIR = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui"
sys.path.insert(0, SCRIPT_DIR)

from sync_stage_engine_kokoro import get_kokoro_engine, speak_kokoro

FIFO_PATH = "/tmp/kokoro_speech_fifo"

def main():
    # Pre-load the model into RAM to completely eliminate synthesis latency (zero gaps)
    print("Loading Kokoro ONNX model into RAM for zero-gap Hot-Standby...", file=sys.stderr)
    engine = get_kokoro_engine()
    print("Model loaded. Hot-Standby Daemon online.", file=sys.stderr)
    
    if not os.path.exists(FIFO_PATH):
        os.mkfifo(FIFO_PATH)
        
    while True:
        with open(FIFO_PATH, "r") as fifo:
            for line in fifo:
                line = line.strip()
                if not line: continue
                try:
                    payload = json.loads(line)
                    agent = payload.get("agent", "maxx")
                    text = payload.get("text", "")
                    if text:
                        speak_kokoro(agent, text)
                except Exception as e:
                    print(f"Daemon Error: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
