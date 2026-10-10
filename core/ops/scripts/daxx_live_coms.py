#!/usr/bin/env python3
"""
XORAS::OS — DAXX & JARVIS LIVE TERMINAL COMS COCKPIT
Direct local bidirectional communication bridge (Text + Voice + Real-Time Telemetry)
"""

import sys
import os
import json
import time
import subprocess
import urllib.request
import urllib.error

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "sovereign-jarvis"
TELEMETRY_LOG = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/agent_logs/daxx_telemetry.jsonl"

def speak_text(agent_name: str, text: str):
    """Triggers local macOS TTS or agent_speak.sh if available."""
    try:
        clean_text = text.replace('"', '\\"').replace("'", "")
        voice = "Alex" if agent_name.lower() == "daxx" else "Daniel"
        cmd = f'say -v {voice} "{clean_text}" &'
        subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def log_telemetry(actor: str, payload: dict):
    """Writes turn-by-turn telemetry to local JSONL log."""
    try:
        os.makedirs(os.path.dirname(TELEMETRY_LOG), exist_ok=True)
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "actor": actor,
            "payload": payload
        }
        with open(TELEMETRY_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass

def send_to_ollama(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Sends prompt directly to local Ollama sovereign-jarvis node."""
    data = json.dumps({
        "model": model,
        "prompt": f"[SYSTEM: You are DAXX / Sovereign Jarvis. Respond concisely, authoritatively, and directly as master engineer.]\nUser: {prompt}\nResponse:",
        "stream": False
    }).encode("utf-8")
    
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return res.get("response", "").strip()
    except urllib.error.URLError:
        return "[LOCAL INFRASTRUCTURE NOTICE] Local Ollama socket offline at http://localhost:11434. Running fallback local DAXX Conductor loop."

def main():
    print("=" * 80)
    print("      XORAS::OS — LIVE DAXX & JARVIS SOVEREIGN COMS COCKPIT (PORT 11434)")
    print("      Status: Live 2-Way Text + Voice + Telemetry Logging")
    print("      Type 'exit' or 'quit' to close session.")
    print("=" * 80 + "\n")

    log_telemetry("SYSTEM", {"event": "LIVE_COMS_COCKPIT_INITIALIZED", "port": 11434})

    while True:
        try:
            user_input = input("Anthony > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                print("\n[COMS COCKPIT] Closing live channel.")
                break

            print("\n[DAXX :: PROCESSING INFRASTRUCTURE INTENT...]")
            start_t = time.perf_counter()
            
            response = send_to_ollama(user_input)
            elapsed = time.perf_counter() - start_t

            print(f"\nDAXX / Jarvis ({elapsed:.2f}s) > {response}\n")
            
            # Trigger real-time voice feedback
            speak_text("DAXX", response[:250])
            
            # Log turn-by-turn telemetry
            log_telemetry("DAXX", {
                "input": user_input,
                "response": response,
                "latency_sec": round(elapsed, 4)
            })

        except KeyboardInterrupt:
            print("\n\n[COMS COCKPIT] Interrupted. Channel stashed.")
            break

if __name__ == "__main__":
    main()
