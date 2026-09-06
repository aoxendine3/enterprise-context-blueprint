#!/usr/bin/env python3
"""
Canonical speech queue consumer.

Reads new queue entries from scratch/speech_queue.txt and dispatches them
through agent_speak.sh one-at-a-time (no overlap), with duplicate suppression.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from collections import deque
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
QUEUE_FILE = ROOT / "scratch/speech_queue.txt"
STATE_FILE = ROOT / "ops/scripts/fullscreen_ui/current_image.txt"
SPEAK_SCRIPT = ROOT / "ops/scripts/agent_speak.sh"
EVENT_LOG = ROOT / "memory/agent_logs/voice_daemon_events.jsonl"

POLL_SECONDS = 0.25
DEDUP_WINDOW_SECONDS = 8.0
DISPATCH_TIMEOUT_SECONDS = 240

PLACEHOLDER_BLOCKLIST = {
    "standing by",
    "operational on metal",
    "ready to execute",
    "readiness check complete",
}


def now() -> float:
    return time.time()


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def write_event(event: str, **details: object) -> None:
    EVENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp": now_iso(), "event": event, **details}
    with EVENT_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def parse_queue_line(raw_line: str) -> tuple[str, str] | tuple[None, None]:
    line = raw_line.strip()
    if not line or "|" not in line:
        return None, None
    agent, text = line.split("|", 1)
    agent = agent.strip().lower()
    text = text.strip()
    if not agent or not text:
        return None, None
    return agent, text


def is_placeholder(text: str) -> bool:
    return normalize(text) in PLACEHOLDER_BLOCKLIST


def queue_fingerprint(agent: str, text: str) -> str:
    norm = f"{agent}|{normalize(text)}"
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


def follow_new_lines(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.touch()

    with path.open("r", encoding="utf-8") as handle:
        handle.seek(0, os.SEEK_END)
        while True:
            line = handle.readline()
            if line:
                yield line
            else:
                time.sleep(POLL_SECONDS)


def run() -> None:
    recent = deque()  # (timestamp, fingerprint)
    write_event("voice-daemon-start")

    for raw_line in follow_new_lines(QUEUE_FILE):
        agent, text = parse_queue_line(raw_line)
        if not agent or not text:
            write_event("skip-invalid-line", raw_line=raw_line.rstrip("\n"))
            continue

        if is_placeholder(text):
            write_event("skip-placeholder", agent=agent, text=text)
            continue

        fingerprint = queue_fingerprint(agent, text)
        current = now()
        while recent and (current - recent[0][0]) > DEDUP_WINDOW_SECONDS:
            recent.popleft()
        if any(fp == fingerprint for _, fp in recent):
            write_event("skip-duplicate", agent=agent, fingerprint=fingerprint)
            continue
        recent.append((current, fingerprint))

        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            STATE_FILE.write_text(agent, encoding="utf-8")
        except OSError as error:
            write_event("state-file-write-error", error=str(error))

        try:
            subprocess.run(
                ["bash", str(SPEAK_SCRIPT), agent, text],
                check=False,
                stdin=subprocess.DEVNULL,
                timeout=DISPATCH_TIMEOUT_SECONDS,
            )
            write_event("dispatch", agent=agent, fingerprint=fingerprint)
        except subprocess.TimeoutExpired:
            write_event("dispatch-timeout", agent=agent, fingerprint=fingerprint)
        except OSError as error:
            write_event("dispatch-error", agent=agent, error=str(error))


if __name__ == "__main__":
    run()
