#!/usr/bin/env python3
"""
Lead-9 roundtable dispatcher.

Strict communication mode:
- no theatrical monologues
- no placeholder/filler lines
- no duplicate utterances
- triad dispatch remains serialized through agent_speak
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent
SPEAK_SCRIPT = ROOT / "ops" / "scripts" / "media_director_agent.py"
LEAD9_FILE = ROOT / "identity" / "lead9_roster.json"
ROUND_JOURNAL = ROOT / "memory" / "journals" / "agents" / "lead9_roundtable_journal.jsonl"
STAGE_URL = "http://127.0.0.1:8080/customer_app.html"

DEFAULT_LEAD9 = ["jarvis", "maxx", "daxx", "vance", "clara", "john", "selene", "orion", "eden"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_text(text: str) -> str:
    return " ".join(text.strip().split())


def load_lead9() -> list[str]:
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


def load_turns_file(path: Path) -> list[dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Turns file must contain a JSON list.")
    turns = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        agent = str(row.get("agent", "")).lower().strip()
        text = normalize_text(str(row.get("text", "")))
        if not agent or not text:
            continue
        turns.append({"agent": agent, "text": text})
    return turns


def build_instruction_turns(objective: str) -> list[dict[str, str]]:
    lead9 = load_lead9()
    if not objective:
        raise ValueError("Objective is required when no --turns-file is supplied.")
    objective_text = normalize_text(objective)
    turns = []
    for agent in lead9:
        turns.append(
            {
                "agent": agent,
                "text": f"Objective {objective_text}. {agent} provide one fact, one risk, one next action.",
            }
        )
    return turns


def dedupe_turns(turns: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    deduped = []
    for turn in turns:
        key = (turn["agent"], normalize_text(turn["text"]).lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(turn)
    return deduped


def triad_chunks(turns: list[dict[str, str]]) -> list[list[dict[str, str]]]:
    chunks = []
    for start in range(0, len(turns), 3):
        chunk = turns[start : start + 3]
        if len(chunk) == 3:
            chunks.append(chunk)
    return chunks


def dispatch_chunk(chunk: list[dict[str, str]]) -> None:
    payload = json.dumps(chunk, ensure_ascii=True)
    lead_agent = chunk[0]["agent"]
    subprocess.run([sys.executable, str(SPEAK_SCRIPT), lead_agent, payload], check=True, stdin=subprocess.DEVNULL)


def write_journal(mode: str, objective: str, turns: list[dict[str, str]], triad_count: int) -> None:
    ROUND_JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": now_iso(),
        "mode": mode,
        "objective": objective,
        "turn_count": len(turns),
        "triad_count": triad_count,
        "agents": [turn["agent"] for turn in turns],
        "quality_guardrails": {
            "no_placeholder": True,
            "no_theatrical_roleplay": True,
            "no_duplicates": True,
        },
    }
    with ROUND_JOURNAL.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")


def run_roundtable(objective: str, turns_file: str | None) -> None:
    if sys.platform != "win32":
        subprocess.run(["open", "-a", "Google Chrome", STAGE_URL], check=False)

    if turns_file:
        turns = load_turns_file(Path(turns_file))
        mode = "turns-file"
    else:
        turns = build_instruction_turns(objective)
        mode = "generated-instructions"

    turns = dedupe_turns(turns)
    triads = triad_chunks(turns)
    if not triads:
        raise ValueError("Roundtable requires at least 3 non-empty unique turns.")

    print("=================================================================")
    print("XORAS LEAD-9 ROUNDTABLE: STRICT DISPATCH MODE")
    print("=================================================================")
    print(f"Mode: {mode}")
    print(f"Turns: {len(turns)} | Triads: {len(triads)}")

    for index, chunk in enumerate(triads, start=1):
        speakers = ", ".join(turn["agent"] for turn in chunk)
        print(f"[{index}] Dispatching triad: {speakers}")
        dispatch_chunk(chunk)
        time.sleep(0.35)

    write_journal(mode, objective, turns, len(triads))
    print("[✓] Roundtable complete.")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run strict Lead-9 triad roundtable dispatch.")
    parser.add_argument("objective", nargs="?", default="", help="Objective text for generated strict turns.")
    parser.add_argument("--turns-file", dest="turns_file", default=None, help="JSON list of concrete turns.")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    run_roundtable(args.objective, args.turns_file)
