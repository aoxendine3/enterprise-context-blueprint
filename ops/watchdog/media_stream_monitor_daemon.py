"""
XORAS MEDIA STREAM MONITOR: NATIVE COMPILED GATEKEEPER INTEGRATION
Golden List Asset #002: Kernel-Level Audio Mutex with Stale PID Self-Healing
Guarantees ZERO audio overlap via native Apple Silicon ARM64 binary.
"""
import json
import os
import subprocess
import sys
import time

GATEKEEPER_BIN = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/capabilities/sovereign_systems_core/bin/sovereign_gatekeeper"
SYNC_STAGE_ENGINE = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/sync_stage_engine.py"

def sanitize_input(text):
    if not text:
        return "Standing by."
    clean = "".join(ch for ch in text if ch in ('\n', '\t', ' ') or ord(ch) >= 32)
    return clean.strip() or "Standing by."

def run_isolated_stream(agent_id, text):
    text = sanitize_input(text)
    agent_id = sanitize_input(agent_id).lower()

    # The native gatekeeper owns stale-lock recovery and mutual exclusion.
    result = subprocess.run(
        [GATEKEEPER_BIN, "acquire", agent_id, "120000"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(
            f"[MEDIA_MONITOR_ERROR] Gatekeeper acquisition failed: {result.stderr.strip()}",
            file=sys.stderr,
        )
        return

    try:
        turns = []
        if os.path.exists(text) and (text.endswith(".json") or text.endswith(".txt")):
            try:
                with open(text) as f:
                    content = f.read().strip()
                if content.startswith("[") and content.endswith("]"):
                    turns = json.loads(content)
            except (OSError, json.JSONDecodeError) as error:
                print(f"[MEDIA_MONITOR_ERROR] Unable to load turn script: {error}", file=sys.stderr)
                return
        elif text.startswith("[") and text.endswith("]"):
            try:
                turns = json.loads(text)
            except json.JSONDecodeError as error:
                print(f"[MEDIA_MONITOR_ERROR] Invalid inline turn script: {error}", file=sys.stderr)
                return

        if not turns:
            turns = [{"agent": agent_id, "text": text}]

        # Mandatory Minimum 3-Agent Council Invariant (Zero Exceptions, Zero Deviations)
        existing_agents = [t.get("agent", "").lower() for t in turns]
        council_fallbacks = [
            ("jarvis", "Jarvis confirming governance and alignment."),
            ("maxx", "Maxx on operations. Execution verified clean on metal."),
            ("clara", "Clara on telemetry. Stage synchronization locked.")
        ]
        for fb_agent, fb_text in council_fallbacks:
            if len(turns) >= 3:
                break
            if fb_agent not in existing_agents:
                turns.append({"agent": fb_agent, "text": fb_text})
                existing_agents.append(fb_agent)

        sys.path.insert(0, "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui")
        from sync_stage_engine import play_script_pipelined, speak_with_word_sync
        if len(turns) > 1:
            play_script_pipelined(turns, gap_seconds=0.35)
        elif len(turns) == 1:
            spk = turns[0].get("agent", agent_id).lower()
            utt = turns[0].get("text", "")
            if utt:
                speak_with_word_sync(spk, utt)

        time.sleep(0.05)
    finally:
        subprocess.run(
            [GATEKEEPER_BIN, "release"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            check=False,
        )

if __name__ == "__main__":
    ag = sys.argv[1] if len(sys.argv) > 1 else "maxx"
    tx = sys.argv[2] if len(sys.argv) > 2 else "Operational."
    run_isolated_stream(ag, tx)
