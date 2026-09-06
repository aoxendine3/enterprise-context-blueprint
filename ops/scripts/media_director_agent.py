"""
XORAS media director agent.

Single admission point for speech dispatch with strict quality gate:
- rejects empty payloads
- rejects placeholder-only content
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

MONITOR_SCRIPT = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/watchdog/media_stream_monitor_daemon.py"
DIRECTOR_LOG = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/watchdog/media_director_audit.jsonl")
PLACEHOLDER_TEXT = {
    "standing by",
    "operational",
    "operational on metal",
    "ready",
    "ready to execute",
    "readiness check complete",
}


def normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def should_reject(text: str) -> tuple[bool, str]:
    normalized = normalize(text)
    if not normalized:
        return True, "empty"
    if normalized in PLACEHOLDER_TEXT:
        return True, "placeholder"
    return False, ""


def write_audit(entry: dict) -> None:
    DIRECTOR_LOG.parent.mkdir(parents=True, exist_ok=True)
    with DIRECTOR_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")


def direct_broadcast(agent_id: str, text: str) -> int:
    rejected, reason = should_reject(text)
    timestamp = time.time()
    audit_entry = {
        "timestamp": timestamp,
        "director": "MEDIA_DIRECTOR_AGENT",
        "admitted_agent": agent_id,
        "script": text,
        "status": "REJECTED" if rejected else "HANDED_TO_STREAM_MONITOR",
        "reason": reason or None,
    }
    write_audit(audit_entry)

    if rejected:
        return 2

    cmd = ["python3", MONITOR_SCRIPT, agent_id, text]
    completed = subprocess.run(cmd, check=False, stdin=subprocess.DEVNULL)
    return completed.returncode


if __name__ == "__main__":
    ag = sys.argv[1] if len(sys.argv) > 1 else "maxx"
    tx = sys.argv[2] if len(sys.argv) > 2 else ""
    raise SystemExit(direct_broadcast(ag, tx))
