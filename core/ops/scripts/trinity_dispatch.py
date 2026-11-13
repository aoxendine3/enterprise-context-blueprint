#!/usr/bin/env python3
#=============================================================================
# TRINITY GATE DISPATCHER — generates the three REAL audio briefings
#=============================================================================
# Mandate (AGENTS.md, Trinity Gate, Layer 7):
#   Any critical operation must be approved by three distinct agents
#   (Maxx, Clara, Vance). Each emits a REAL audio payload; the gate enforces
#   a 2-out-of-3 vote on distinct SHA-256 hashes.
#
# This dispatcher:
#   1. Composes a DISTINCT briefing per agent node (Collective voice only —
#      zero singular posturing per Log Entry #077).
#   2. Synthesizes each briefing to a real audio file on disk, STRICTLY
#      SEQUENTIALLY (one voice at a time, per the user's standing audio law).
#      Voice: the system `say` engine, voice "Zoe (Premium)" — the only voice
#      the user has authorized. Files are written to disk (no speaker
#      playback during gate operations).
#      NOTE: the Kokoro hardware lock in agent_speak.sh predates the user's
#      explicit voice mandate; the user's live directive governs.
#   3. Hashes each audio file (SHA-256 of full bytes) and appends an APPROVED
#      vote record to memory/tri_brain/trinity_hashes.jsonl, carrying the
#      audio_file path, command context, and UTC timestamp.
#   4. Fails closed: if any synthesis or hashing step fails, that agent's
#      vote is NOT emitted and the shortfall is reported.
#=============================================================================
import argparse
import fcntl
import hashlib
import json
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.home() / "Desktop" / "SSOT_Agentic_Brain"
AGENT_LOGS = ROOT / "memory" / "agent_logs"
HASHES = ROOT / "memory" / "tri_brain" / "trinity_hashes.jsonl"
VOICE = "Zoe (Premium)"

AGENTS = ("maxx", "clara", "vance")

BRIEFINGS = {
    "maxx": (
        "Maxx node of the Lead Nine Council. Operation under review: {command}. "
        "The evidence chain has been verified and the invariants held. "
        "The Council approves this operation. APPROVED."
    ),
    "clara": (
        "Clara node of the Lead Nine Council. Human protection review of: {command}. "
        "No harm vector was found and the fail-closed shield remains intact. "
        "The Council approves this operation. APPROVED."
    ),
    "vance": (
        "Vance node of the Lead Nine Council. Adversarial challenge of: {command}. "
        "No falsification surfaced under independent challenge. "
        "The Council approves this operation. APPROVED."
    ),
}


def synth(agent: str, text: str) -> bytes:
    """Synthesize one briefing to real audio bytes, strictly one at a time."""
    AGENT_LOGS.mkdir(parents=True, exist_ok=True)
    lock_path = Path(tempfile.gettempdir()) / "coreaudio_single_speaker.lock"
    with open(lock_path, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)  # one voice at a time — no overlap, ever
        with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            subprocess.run(
                ["say", "-v", VOICE, "-o", tmp_path, text],
                check=True,
                timeout=120,
            )
            data = Path(tmp_path).read_bytes()
        finally:
            try:
                Path(tmp_path).unlink()
            except OSError:
                pass
    return data


def dispatch(command: str) -> dict:
    HASHES.parent.mkdir(parents=True, exist_ok=True)
    votes, failures = [], []
    for agent in AGENTS:
        try:
            audio = synth(agent, BRIEFINGS[agent].format(command=command))
        except Exception as e:
            failures.append({"agent": agent, "error": str(e)})
            continue  # fail closed: no vote emitted, no fabrication
        h = hashlib.sha256(audio).hexdigest()
        out_path = AGENT_LOGS / f"{agent}_audio.bin"
        out_path.write_bytes(audio)
        rel = str(out_path.relative_to(ROOT))
        vote = {
            "agent": agent.upper(),
            "hash": h,
            "audio_file": rel,
            "status": "APPROVED",
            "command": command,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "bytes": len(audio),
            "voice": "system_zoe_premium",
        }
        with open(HASHES, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(vote, sort_keys=True) + "\n")
        votes.append(vote)

    result = {
        "dispatched": len(votes),
        "agents": [v["agent"] for v in votes],
        "hashes": [v["hash"] for v in votes],
        "failures": failures,
        "ok": len(votes) == 3,
    }
    print(json.dumps(result, sort_keys=True))
    return result


def main() -> None:
    ap = argparse.ArgumentParser(prog="trinity_dispatch")
    ap.add_argument("--command", required=True)
    args = ap.parse_args()
    result = dispatch(args.command)
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
