#!/usr/bin/env python3
"""
=============================================================================
TURN LEDGER — WHAT EVERY AGENT IS DOING, RIGHT NOW
=============================================================================
Every collective turn is recorded with its phase and its declared intent:
  • what the agent was about to do   ([NEXT])
  • what the agent actually did      ([BREAKDOWN])
  • what happens next                ([NEXT] / [SUMMARY])

The ledger is append-only and answers the operator's standing question —
"what is my agent doing?" — without guessing and without asking the agent.

Usage:
  turn_ledger.py --agent maxx --phase NEXT --text "..."
  turn_ledger.py --status
  turn_ledger.py --agent maxx
=============================================================================
"""

import argparse
import json
import re
import time
from pathlib import Path

# Resolve from this file so the wake path survives a checkout anywhere.
ROOT = Path(__file__).resolve().parents[3]
LEDGER = ROOT / "memory" / "agent_logs" / "turn_ledger.jsonl"

DID_RE = re.compile(r"\b(did|done|completed|landed|fixed|repaired|closed|passed|found|restored|verified|written|built|ran|walked|opened|measured|audited|counted|catalogued|rebuilt|rewired|spoke|read|captured|traced|mapped|cleaned|quarantined)\b", re.IGNORECASE)
NEXT_RE = re.compile(r"\bnext\b", re.IGNORECASE)


def extract_next(text: str) -> str:
    """Pull the sentence that states what happens next."""
    for sentence in re.split(r"(?<=[.!?])\s+", text or ""):
        if NEXT_RE.search(sentence):
            return sentence.strip()[:400]
    return ""


def extract_did(text: str) -> str:
    """Pull the sentence that states what was actually done."""
    for sentence in re.split(r"(?<=[.!?])\s+", text or ""):
        if DID_RE.search(sentence):
            return sentence.strip()[:400]
    return ""


def record(agent: str, phase: str, text: str) -> dict:
    entry = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "schema": "xoras.turn.v1",
        "agent": agent,
        "phase": phase,
        "did": extract_did(text),
        "next": extract_next(text),
        "excerpt": (text or "")[:280],
    }
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry


def load() -> list:
    rows = []
    if not LEDGER.exists():
        return rows
    with open(LEDGER, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def status(agent: str = None) -> dict:
    rows = load()
    if agent:
        rows = [r for r in rows if r.get("agent") == agent]
    by_agent: dict = {}
    for r in rows:
        a = r.get("agent", "collective")
        slot = by_agent.setdefault(a, {"turns": 0, "last_phase": None, "last_ts": None,
                                      "doing_next": "", "last_done": "", "last_excerpt": ""})
        slot["turns"] += 1
        slot["last_phase"] = r.get("phase")
        slot["last_ts"] = r.get("timestamp_utc")
        if r.get("next"):
            slot["doing_next"] = r["next"]
        if r.get("did"):
            slot["last_done"] = r["did"]
        if r.get("excerpt"):
            slot["last_excerpt"] = r["excerpt"]
    return by_agent


def main() -> int:
    ap = argparse.ArgumentParser(description="turn ledger")
    ap.add_argument("--agent")
    ap.add_argument("--phase", default="BREAKDOWN")
    ap.add_argument("--text")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()

    if args.status or (not args.text):
        data = status(args.agent)
        if not data:
            print("no turns recorded yet")
            return 0
        for agent, s in sorted(data.items()):
            print(f"\n> {agent}  ({s['turns']} turns | last {s['last_phase']} @ {s['last_ts']})")
            if s["last_done"]:
                print(f"   done : {s['last_done'][:160]}")
            if s["doing_next"]:
                print(f"   next : {s['doing_next'][:160]}")
        return 0

    entry = record(args.agent or "collective", args.phase, args.text)
    print(f"turn recorded: {entry['agent']} / {entry['phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
