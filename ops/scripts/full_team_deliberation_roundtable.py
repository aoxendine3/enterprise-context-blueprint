#!/usr/bin/env python3
"""
XORAS LEAD-9 ROUNDTABLE ORCHESTRATOR
- Always dispatches at least three speakers per broadcast payload.
- Rotates the Lead 9 roster with light randomization for non-rigid sessions.
- Writes a daily journal receipt with humor + dream seed for continuity.
"""

import json
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
SPEAK_SCRIPT = ROOT / "ops/scripts/agent_speak.sh"
STAGE_URL = "http://127.0.0.1:8080/customer_app.html"
LEAD9_FILE = ROOT / "identity/lead9_roster.json"
ROUND_JOURNAL = ROOT / "memory/journals/agents/lead9_roundtable_journal.jsonl"

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

ROLE_MAP = {
    "jarvis": "governance chair",
    "maxx": "operations lead",
    "daxx": "engineering remediation lead",
    "vance": "falsification and audit lead",
    "clara": "research and ethics lead",
    "john": "silicon telemetry lead",
    "selene": "conversation resonance lead",
    "orion": "media routing lead",
    "eden": "integrity and heartbeat lead",
}

HUMOR_SPARKS = [
    "No chaos monkeys in production without a badge and a checklist.",
    "If a bug survives Vance and Daxx together, it at least deserves a name tag.",
    "We are fast, but we still read the logs before celebrating.",
]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_lead9():
    try:
        payload = json.loads(LEAD9_FILE.read_text(encoding="utf-8"))
        entries = payload.get("lead_9", [])
        ordered = [str(entry.get("agent_id", "")).lower().strip() for entry in entries if entry.get("agent_id")]
        ordered = [agent for agent in ordered if agent]
        if len(ordered) >= 3:
            return ordered
    except (OSError, json.JSONDecodeError):
        pass
    return DEFAULT_LEAD9.copy()


def select_order():
    lead9 = load_lead9()
    # Deterministic daily rotation + stochastic shuffle for the remaining seats.
    rotation = int(time.time() // 86400) % len(lead9)
    rotated = lead9[rotation:] + lead9[:rotation]
    lead = rotated[0]
    rest = rotated[1:]
    random.SystemRandom().shuffle(rest)
    return lead, [lead] + rest


def make_turn(agent, lead, focus, humor_line):
    role = ROLE_MAP.get(agent, "council specialist")
    lead_clause = f"Lead seat is {lead.upper()} for this cycle."
    focus_clause = f"Focus: {focus}" if focus else "Focus: intake, verify, execute, document."
    return {
        "agent": agent,
        "text": (
            f"{agent.title()} on {role}. {lead_clause} {focus_clause} "
            f"Readiness check complete; evidence and ownership are active. {humor_line}"
        ),
    }


def build_turns(focus):
    lead, order = select_order()
    humor_line = random.choice(HUMOR_SPARKS)
    turns = [make_turn(agent, lead, focus, humor_line) for agent in order]
    return lead, order, turns, humor_line


def triad_chunks(turns):
    chunks = []
    for start in range(0, len(turns), 3):
        chunk = turns[start : start + 3]
        if len(chunk) < 3:
            needed = 3 - len(chunk)
            chunk.extend(turns[:needed])
        chunks.append(chunk)
    return chunks


def write_journal(lead, order, focus, humor_line):
    ROUND_JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": now_iso(),
        "lead_agent": lead,
        "order": order,
        "focus": focus or "general operations",
        "humor_line": humor_line,
        "dream_seed": f"Dream on this focus tonight: {focus or 'stronger coordination with less noise'}.",
    }
    with ROUND_JOURNAL.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def dispatch_chunk(chunk):
    payload = json.dumps(chunk, ensure_ascii=True)
    lead_agent = chunk[0]["agent"]
    subprocess.run(["bash", str(SPEAK_SCRIPT), lead_agent, payload], check=True, stdin=subprocess.DEVNULL)


def run_roundtable(focus):
    print("=================================================================")
    print("XORAS LEAD-9 ROUNDTABLE: TRIAD CYCLE DISPATCH")
    print("=================================================================")

    subprocess.run(["open", "-a", "Google Chrome", STAGE_URL], check=False)
    lead, order, turns, humor_line = build_turns(focus)

    for index, chunk in enumerate(triad_chunks(turns), start=1):
        speakers = ", ".join(turn["agent"] for turn in chunk)
        print(f"[{index}] Dispatching triad: {speakers}")
        dispatch_chunk(chunk)
        time.sleep(0.4)

    write_journal(lead, order, focus, humor_line)
    print(f"[✓] Roundtable complete. Lead={lead}, turns={len(turns)}, triads={len(triad_chunks(turns))}")


if __name__ == "__main__":
    focus = " ".join(sys.argv[1:]).strip()
    run_roundtable(focus)

