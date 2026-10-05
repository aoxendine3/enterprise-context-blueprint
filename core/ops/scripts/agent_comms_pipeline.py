#!/usr/bin/env python3
"""
Canonical SSOT communication pipeline (STT -> routing -> monitoring).

Design goals:
1. No overlapping speech (single outbound queue + downstream audio mutex).
2. No repeated speech (time-window dedupe).
3. No placeholder/theatrical filler generation.
4. Persistent routing memory and receipts for audit/catch flows.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from queue import Empty, Full, Queue

import speech_recognition as sr

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
SPEECH_QUEUE_FILE = ROOT / "scratch/speech_queue.txt"
ROUTE_LOG_FILE = ROOT / "memory/agent_logs/stt_route_events.jsonl"
INBOX_LOG_FILE = ROOT / "memory/agent_logs/agent_inbox.jsonl"
RECEIPT_LOG_FILE = ROOT / "memory/journals/agents/comms_pipeline_receipts.jsonl"

STOP_PHRASES = ("close mic", "stop listening", "stand down", "shutdown line", "stop")
WAKE_HINTS = ("wake", "wake up", "you up", "are you there")

ROUTE_RULES = (
    ("jarvis", ("governance", "policy", "decision", "arbitrate")),
    ("maxx", ("ops", "operation", "execute", "run", "deploy")),
    ("daxx", ("code", "bug", "debug", "refactor", "script", "build")),
    ("john", ("weather", "forecast", "latency", "metric", "telemetry")),
    ("clara", ("research", "ethic", "strategy", "explain")),
    ("orion", ("route", "broadcast", "stage", "audio", "voice")),
    ("selene", ("conversation", "tone", "human", "rapport", "care")),
)

AGENT_ALIASES = {
    "jarvis": ("jarvis",),
    "maxx": ("maxx", "max "),
    "daxx": ("daxx",),
    "vance": ("vance",),
    "clara": ("clara",),
    "john": ("john",),
    "orion": ("orion",),
    "selene": ("selene",),
    "eden": ("eden",),
}

PLACEHOLDER_TEXT = {
    "standing by",
    "ready",
    "ready to execute",
    "operational",
    "operational on metal",
}

IDLE_TIMEOUT_SECONDS = int(os.environ.get("SSOT_COMMS_IDLE_TIMEOUT_SECONDS", "300"))
HEARTBEAT_SECONDS = int(os.environ.get("SSOT_COMMS_HEARTBEAT_SECONDS", "5"))
DEDUPE_WINDOW_SECONDS = float(os.environ.get("SSOT_COMMS_DEDUPE_WINDOW_SECONDS", "8"))
MIN_TEXT_CHARS = int(os.environ.get("SSOT_COMMS_MIN_TEXT_CHARS", "3"))
SPEAK_ROUTE_ACKS = os.environ.get("SSOT_COMMS_SPEAK_ROUTE_ACKS", "0").strip() == "1"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_text(text: str) -> str:
    lowered = text.lower().strip()
    lowered = re.sub(r"\s+", " ", lowered)
    lowered = re.sub(r"[^a-z0-9\s'_-]", "", lowered)
    return lowered


def write_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def append_speech_queue(agent: str, text: str) -> None:
    SPEECH_QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with SPEECH_QUEUE_FILE.open("a", encoding="utf-8") as handle:
        handle.write(f"{agent}|{text}\n")


@dataclass
class PipelineState:
    active_agent: str = "maxx"
    last_input_at: float = field(default_factory=time.time)
    last_route_at: float = 0.0
    last_line: str = ""
    shutdown_reason: str = ""
    total_inputs: int = 0
    total_routes: int = 0
    total_dropped: int = 0
    recent_fingerprints: deque = field(default_factory=deque)
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def mark_input(self, line: str) -> None:
        with self.lock:
            self.last_input_at = time.time()
            self.last_line = line
            self.total_inputs += 1

    def mark_route(self) -> None:
        with self.lock:
            self.last_route_at = time.time()
            self.total_routes += 1

    def mark_drop(self) -> None:
        with self.lock:
            self.total_dropped += 1

    def set_active_agent(self, agent: str) -> None:
        with self.lock:
            self.active_agent = agent

    def snapshot(self) -> dict:
        with self.lock:
            return {
                "active_agent": self.active_agent,
                "last_input_at": self.last_input_at,
                "last_route_at": self.last_route_at,
                "last_line": self.last_line,
                "total_inputs": self.total_inputs,
                "total_routes": self.total_routes,
                "total_dropped": self.total_dropped,
                "shutdown_reason": self.shutdown_reason,
            }

    def set_shutdown_reason(self, reason: str) -> None:
        with self.lock:
            self.shutdown_reason = reason

    def duplicate_seen(self, fingerprint: str) -> bool:
        now = time.time()
        with self.lock:
            while self.recent_fingerprints and (now - self.recent_fingerprints[0][0]) > DEDUPE_WINDOW_SECONDS:
                self.recent_fingerprints.popleft()
            if any(fp == fingerprint for _, fp in self.recent_fingerprints):
                return True
            self.recent_fingerprints.append((now, fingerprint))
            return False


def detect_wake_target(text: str) -> str | None:
    line = text.lower().strip()
    if not any(hint in line for hint in WAKE_HINTS):
        return None
    if "jarvis" in line:
        return "jarvis"
    if "maxx" in line or "max " in f"{line} " or line == "max":
        return "maxx"
    return "maxx"


def should_stop(text: str) -> bool:
    line = text.lower()
    return any(phrase in line for phrase in STOP_PHRASES)


def select_route_target(text: str, active_agent: str) -> tuple[str, str]:
    line = text.lower()

    for agent, aliases in AGENT_ALIASES.items():
        if any(alias in line for alias in aliases):
            return agent, "explicit-agent"

    for agent, keywords in ROUTE_RULES:
        for keyword in keywords:
            if keyword in line:
                return agent, f"keyword:{keyword}"

    return active_agent, "active-agent-fallback"


def is_placeholder(text: str) -> bool:
    normalized = normalize_text(text)
    return normalized in PLACEHOLDER_TEXT


def queue_wake_ack(agent: str) -> None:
    ack = f"wake acknowledged. active agent set to {agent}. send objective."
    append_speech_queue(agent, ack)


def mic_intake_node(events: Queue, shutdown: threading.Event, state: PipelineState) -> None:
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 4000
    recognizer.dynamic_energy_threshold = True

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        while not shutdown.is_set():
            try:
                audio = recognizer.listen(source, timeout=2, phrase_time_limit=10)
                line = recognizer.recognize_google(audio).strip().lower()
                if len(line) < MIN_TEXT_CHARS:
                    continue
                state.mark_input(line)
                event = {"timestamp": now_iso(), "text": line}
                try:
                    events.put(event, timeout=0.5)
                except Full:
                    state.mark_drop()
                    write_jsonl(
                        ROUTE_LOG_FILE,
                        {
                            "timestamp": now_iso(),
                            "kind": "drop",
                            "reason": "event-queue-full",
                            "text": line,
                        },
                    )
                    continue
                print(f"[TRANSCRIPT] -> {line}", flush=True)
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except sr.RequestError as error:
                print(f"[NODE1:ERROR] STT API error: {error}", flush=True)
                time.sleep(1)
            except Exception as error:
                print(f"[NODE1:ERROR] Mic intake failure: {error}", flush=True)
                time.sleep(1)


def router_node(events: Queue, shutdown: threading.Event, state: PipelineState) -> None:
    while not shutdown.is_set():
        try:
            event = events.get(timeout=1)
        except Empty:
            continue

        text = event["text"]
        normalized = normalize_text(text)
        fingerprint = f"stt:{normalized}"

        if state.duplicate_seen(fingerprint):
            state.mark_drop()
            write_jsonl(
                ROUTE_LOG_FILE,
                {
                    "timestamp": now_iso(),
                    "kind": "drop",
                    "reason": "duplicate",
                    "text": text,
                },
            )
            events.task_done()
            continue

        if should_stop(text):
            state.set_shutdown_reason(f"voice-stop:{text}")
            write_jsonl(
                RECEIPT_LOG_FILE,
                {
                    "timestamp": now_iso(),
                    "event": "shutdown",
                    "reason": state.snapshot()["shutdown_reason"],
                },
            )
            print("[NODE2] Stop phrase received; shutting down pipeline.", flush=True)
            shutdown.set()
            events.task_done()
            continue

        wake_target = detect_wake_target(text)
        if wake_target:
            state.set_active_agent(wake_target)
            state.mark_route()
            queue_wake_ack(wake_target)
            write_jsonl(
                ROUTE_LOG_FILE,
                {
                    "timestamp": now_iso(),
                    "kind": "wake",
                    "target": wake_target,
                    "input": text,
                },
            )
            print(f"[NODE2] Wake routed -> {wake_target}", flush=True)
            events.task_done()
            continue

        if is_placeholder(text):
            state.mark_drop()
            write_jsonl(
                ROUTE_LOG_FILE,
                {
                    "timestamp": now_iso(),
                    "kind": "drop",
                    "reason": "placeholder-input",
                    "text": text,
                },
            )
            events.task_done()
            continue

        snapshot = state.snapshot()
        target, reason = select_route_target(text, snapshot["active_agent"])
        state.mark_route()

        inbox_entry = {
            "timestamp": now_iso(),
            "target": target,
            "reason": reason,
            "input": text,
            "active_agent": snapshot["active_agent"],
        }
        write_jsonl(INBOX_LOG_FILE, inbox_entry)
        write_jsonl(
            ROUTE_LOG_FILE,
            {
                "timestamp": now_iso(),
                "kind": "route",
                "target": target,
                "reason": reason,
                "input": text,
            },
        )

        if SPEAK_ROUTE_ACKS:
            append_speech_queue(target, f"route confirmed: {target}")

        print(f"[NODE2] Routed -> {target} ({reason})", flush=True)
        events.task_done()


def monitor_node(
    events: Queue,
    shutdown: threading.Event,
    state: PipelineState,
    intake_thread: threading.Thread,
    route_thread: threading.Thread,
) -> None:
    while not shutdown.is_set():
        time.sleep(HEARTBEAT_SECONDS)
        snap = state.snapshot()
        idle_seconds = time.time() - snap["last_input_at"]
        queue_depth = events.qsize()
        print(
            f"[NODE3] heartbeat active={snap['active_agent']} queue={queue_depth} idle={idle_seconds:.1f}s "
            f"routes={snap['total_routes']} drops={snap['total_dropped']}",
            flush=True,
        )

        if not intake_thread.is_alive():
            state.set_shutdown_reason("intake-thread-exited")
            print("[NODE3] Intake node exited unexpectedly; shutting down.", flush=True)
            shutdown.set()
            break
        if not route_thread.is_alive():
            state.set_shutdown_reason("router-thread-exited")
            print("[NODE3] Router node exited unexpectedly; shutting down.", flush=True)
            shutdown.set()
            break
        if idle_seconds >= IDLE_TIMEOUT_SECONDS and queue_depth == 0:
            state.set_shutdown_reason("idle-timeout")
            print("[NODE3] Idle timeout reached; auto-standby engaged.", flush=True)
            shutdown.set()
            break


def run_pipeline() -> None:
    SPEECH_QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    ROUTE_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    INBOX_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not SPEECH_QUEUE_FILE.exists():
        SPEECH_QUEUE_FILE.touch()

    print("\n[COMMS] 3-node pipeline online: intake -> router -> monitor", flush=True)
    print("[COMMS] Wake examples: 'Max wake up', 'Jarvis wake up', 'wake up'.", flush=True)
    print("[COMMS] Stop phrases: 'close mic', 'stop listening', 'stand down'.\n", flush=True)

    state = PipelineState()
    shutdown = threading.Event()
    events: Queue = Queue(maxsize=256)

    intake_thread = threading.Thread(
        target=mic_intake_node,
        args=(events, shutdown, state),
        daemon=True,
        name="comms-intake-node",
    )
    route_thread = threading.Thread(
        target=router_node,
        args=(events, shutdown, state),
        daemon=True,
        name="comms-router-node",
    )
    monitor_thread = threading.Thread(
        target=monitor_node,
        args=(events, shutdown, state, intake_thread, route_thread),
        daemon=True,
        name="comms-monitor-node",
    )

    intake_thread.start()
    route_thread.start()
    monitor_thread.start()

    write_jsonl(
        RECEIPT_LOG_FILE,
        {"timestamp": now_iso(), "event": "start", "idle_timeout_seconds": IDLE_TIMEOUT_SECONDS},
    )

    while not shutdown.is_set():
        time.sleep(0.5)

    snap = state.snapshot()
    write_jsonl(
        RECEIPT_LOG_FILE,
        {
            "timestamp": now_iso(),
            "event": "stop",
            "reason": snap["shutdown_reason"] or "unknown",
            "total_inputs": snap["total_inputs"],
            "total_routes": snap["total_routes"],
            "total_dropped": snap["total_dropped"],
        },
    )
    print(f"\n[COMMS] Pipeline stopping ({snap['shutdown_reason']}).", flush=True)


if __name__ == "__main__":
    try:
        run_pipeline()
    except KeyboardInterrupt:
        print("\n[COMMS] Keyboard interrupt: shutting down.", flush=True)
