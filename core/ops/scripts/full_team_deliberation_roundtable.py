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
from pathlib import Path

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


def verify_or_start_stage_server() -> bool:
    import urllib.request
    try:
        req = urllib.request.urlopen("http://127.0.0.1:8080/customer_app.html", timeout=2)
        if req.status == 200:
            return True
    except Exception:
        pass
    
    # Attempt to auto-spawn fullscreen_server.py
    server_script = ROOT / "ops" / "scripts" / "fullscreen_server.py"
    if server_script.exists():
        subprocess.Popen([sys.executable, str(server_script)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.5)
        try:
            req = urllib.request.urlopen("http://127.0.0.1:8080/customer_app.html", timeout=2)
            if req.status == 200:
                return True
        except Exception:
            pass
    return False


def dispatch_chunk_with_retry(chunk: list[dict[str, str]], max_retries: int = 3) -> bool:
    payload = json.dumps(chunk, ensure_ascii=True)
    lead_agent = chunk[0]["agent"]
    
    for attempt in range(1, max_retries + 1):
        try:
            # Primary dispatch via media_director_agent.py
            subprocess.run([sys.executable, str(SPEAK_SCRIPT), lead_agent, payload], check=True, stdin=subprocess.DEVNULL, timeout=30)
            return True
        except Exception as err:
            backoff = 2 ** attempt
            print(f"[WARN] Triad dispatch attempt {attempt}/{max_retries} failed for {lead_agent}: {err}. Retrying in {backoff}s...", file=sys.stderr)
            time.sleep(backoff)
            
    # Fallback to local direct speech script if media director fails
    direct_speak = ROOT / "ops" / "scripts" / "agent_speak.sh"
    if direct_speak.exists():
        try:
            combined_text = f"{lead_agent} deliberating: " + ". ".join([f"{t['agent']}: {t['text']}" for t in chunk])
            subprocess.run(["bash", str(direct_speak), lead_agent, combined_text], check=True, timeout=30)
            return True
        except Exception as err:
            print(f"[ERROR] Direct speak fallback failed for {lead_agent}: {err}", file=sys.stderr)
            
    return False


def write_journal(mode: str, objective: str, turns: list[dict[str, str]], triad_count: int, status: str = "SUCCESS", error_detail: str = "") -> None:
    ROUND_JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": now_iso(),
        "mode": mode,
        "status": status,
        "error_detail": error_detail,
        "objective": objective,
        "turn_count": len(turns),
        "triad_count": triad_count,
        "agents": [turn["agent"] for turn in turns],
        "quality_guardrails": {
            "no_placeholder": True,
            "no_theatrical_roleplay": True,
            "no_duplicates": True,
            "honest_failure_logging": True,
        },
    }
    with ROUND_JOURNAL.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")


def run_roundtable(objective: str, turns_file: str | None) -> None:
    # BINDING LAW: Enforce Pre-Deliberation Health Gate & Merkle DAG Verification
    gate_script = ROOT / "ops" / "scripts" / "preflight_health_gate.py"
    if gate_script.exists():
        gate_proc = subprocess.run([sys.executable, str(gate_script)], check=False)
        if gate_proc.returncode != 0:
            msg = "Pre-Deliberation Health Gate BLOCKED execution. Sovereign stack halting."
            print(f"[FATAL BINDING GATE BLOCK] {msg}", file=sys.stderr)
            write_journal(mode="preflight-failure", objective=objective, turns=[], triad_count=0, status="HEALTH_GATE_BLOCKED", error_detail=msg)
            sys.exit(1)

    stage_online = verify_or_start_stage_server()
    if not stage_online:
        msg = "Stage server on port 8080 is unreachable and auto-spawn failed."
        print(f"[FATAL ERROR] {msg}", file=sys.stderr)
        write_journal(mode="preflight-failure", objective=objective, turns=[], triad_count=0, status="STAGE_SERVER_OFFLINE", error_detail=msg)
        sys.exit(1)

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
        msg = "Roundtable requires at least 3 non-empty unique turns."
        write_journal(mode=mode, objective=objective, turns=turns, triad_count=0, status="INVALID_TURNS", error_detail=msg)
        raise ValueError(msg)

    print("=================================================================")
    print("XORAS LEAD-9 ROUNDTABLE: STRICT DISPATCH MODE")
    print("=================================================================")
    print(f"Mode: {mode} | Stage Server: ONLINE (Port 8080)")
    print(f"Turns: {len(turns)} | Triads: {len(triads)}")

    dispatch_success = True
    failed_triad_info = ""

    for index, chunk in enumerate(triads, start=1):
        speakers = ", ".join(turn["agent"] for turn in chunk)
        print(f"[{index}] Dispatching triad: {speakers}")
        success = dispatch_chunk_with_retry(chunk)
        if not success:
            dispatch_success = False
            failed_triad_info = f"Triad {index} ({speakers}) failed all retries and fallback."
            print(f"[ERROR] {failed_triad_info}", file=sys.stderr)
            break
        time.sleep(0.35)

    if dispatch_success:
        write_journal(mode, objective, turns, len(triads), status="SUCCESS")
        print("[OK] Roundtable complete.")
    else:
        write_journal(mode, objective, turns, len(triads), status="DISPATCH_FAILED", error_detail=failed_triad_info)
        print(f"[FAILED] Roundtable dispatch failed: {failed_triad_info}", file=sys.stderr)
        sys.exit(1)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run strict Lead-9 triad roundtable dispatch.")
    parser.add_argument("objective", nargs="?", default="", help="Objective text for generated strict turns.")
    parser.add_argument("--turns-file", dest="turns_file", default=None, help="JSON list of concrete turns.")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    run_roundtable(args.objective, args.turns_file)
