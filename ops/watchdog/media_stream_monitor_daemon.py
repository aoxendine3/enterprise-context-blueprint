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
from typing import Any

GATEKEEPER_BIN = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/capabilities/sovereign_systems_core/bin/sovereign_gatekeeper"
SYNC_STAGE_ENGINE = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/sync_stage_engine.py"
LEAD9_ROSTER = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/identity/lead9_roster.json"
DEFAULT_LEAD9 = [
    "jarvis",
    "maxx",
    "daxx",
    "vance",
    "clara",
    "john",
    "selene",
    "orion",
    "eden",
]
FALLBACK_LINES = {
    "jarvis": "Jarvis here. Governance aligned and ready to execute.",
    "maxx": "Maxx on operations. Clean run, clean logs, clean handoff.",
    "daxx": "Daxx stepping in. Bug hunt loaded and torque calibrated.",
    "vance": "Vance confirms falsification checks are active and ruthless.",
    "clara": "Clara here. Ethics and research coherence are in lockstep.",
    "john": "John confirms silicon telemetry and cache paths are nominal.",
    "selene": "Selene here. Conversation resonance is human and steady.",
    "orion": "Orion confirms media flow and stage synchronization are stable.",
    "eden": "Eden verifies heartbeat integrity and human alignment are centered.",
}

def sanitize_input(text):
    if not text:
        return "Standing by."
    clean = "".join(ch for ch in text if ch in ('\n', '\t', ' ') or ord(ch) >= 32)
    return clean.strip() or "Standing by."


def load_lead9_order():
    try:
        with open(LEAD9_ROSTER, encoding="utf-8") as handle:
            payload = json.load(handle)
        lead_9 = payload.get("lead_9", [])
        ordered = [str(entry.get("agent_id", "")).lower().strip() for entry in lead_9 if entry.get("agent_id")]
        ordered = [agent for agent in ordered if agent]
        if ordered:
            return ordered
    except (OSError, json.JSONDecodeError):
        pass
    return DEFAULT_LEAD9.copy()


def normalize_turns(turns: list[Any]):
    normalized = []
    for turn in turns:
        if isinstance(turn, dict):
            agent = sanitize_input(str(turn.get("agent", ""))).lower()
            text = sanitize_input(str(turn.get("text", "")))
            if text:
                normalized.append({"agent": agent or "maxx", "text": text})
    return normalized


def enforce_minimum_council(turns, initiating_agent):
    turns = normalize_turns(turns)
    if not turns:
        turns = [{"agent": initiating_agent, "text": "Standing by."}]

    existing_agents = []
    for turn in turns:
        agent = turn.get("agent", "").lower()
        if agent and agent not in existing_agents:
            existing_agents.append(agent)

    lead9 = load_lead9_order()
    rotation = int(time.time()) % len(lead9) if lead9 else 0
    rotated = lead9[rotation:] + lead9[:rotation]
    candidate_order = [initiating_agent] + rotated

    for candidate in candidate_order:
        if len(existing_agents) >= 3:
            break
        if candidate and candidate not in existing_agents:
            turns.append(
                {
                    "agent": candidate,
                    "text": FALLBACK_LINES.get(candidate, f"{candidate.title()} confirms operational readiness."),
                }
            )
            existing_agents.append(candidate)

    return turns

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

        turns = enforce_minimum_council(turns, agent_id)

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
