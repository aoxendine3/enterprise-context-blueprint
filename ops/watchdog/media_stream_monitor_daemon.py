"""
XORAS media stream monitor with native gatekeeper lock.

This monitor is strict by design:
- no fabricated fallback utterances
- no placeholder lines
- no duplicate utterances in the same dispatch payload
- serialized audio via sovereign gatekeeper + sync stage engine
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SSOT_ROOT = SCRIPT_DIR.parent.parent
GATEKEEPER_BIN = str(SSOT_ROOT / "capabilities" / "sovereign_systems_core" / "bin" / "sovereign_gatekeeper")
PLACEHOLDER_TEXT = {
    "standing by",
    "operational",
    "operational on metal",
    "ready to execute",
    "readiness check complete",
}


def sanitize_input(text: str) -> str:
    clean = "".join(ch for ch in text if ch in ("\n", "\t", " ") or ord(ch) >= 32)
    return clean.strip()


def normalize_text(text: str) -> str:
    return " ".join(text.lower().strip().split())


def is_placeholder(text: str) -> bool:
    return normalize_text(text) in PLACEHOLDER_TEXT


def normalize_turns(turns: list[Any]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for turn in turns:
        if not isinstance(turn, dict):
            continue
        agent = sanitize_input(str(turn.get("agent", ""))).lower() or "maxx"
        text = sanitize_input(str(turn.get("text", "")))
        if not text or is_placeholder(text):
            continue
        fingerprint = (agent, normalize_text(text))
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        normalized.append({"agent": agent, "text": text})

    return normalized


def enforce_minimum_council(turns: list[Any], initiating_agent: str) -> list[dict[str, str]]:
    """
    Kept for API compatibility. No synthetic fallback content is injected.
    """
    normalized = normalize_turns(turns)
    if normalized:
        return normalized

    cleaned = sanitize_input(initiating_agent).lower() or "maxx"
    return [{"agent": cleaned, "text": ""}]


def parse_turn_script_payload(raw_text: str) -> list[dict[str, str]]:
    turns: list[Any] = []
    if os.path.exists(raw_text) and (raw_text.endswith(".json") or raw_text.endswith(".txt")):
        with open(raw_text, encoding="utf-8") as handle:
            content = handle.read().strip()
        if content.startswith("[") and content.endswith("]"):
            turns = json.loads(content)
    elif raw_text.startswith("[") and raw_text.endswith("]"):
        turns = json.loads(raw_text)

    return normalize_turns(turns)


def run_isolated_stream(agent_id: str, text: str) -> None:
    cleaned_agent = sanitize_input(agent_id).lower() or "maxx"
    cleaned_text = sanitize_input(text)

    has_gatekeeper = os.path.isfile(GATEKEEPER_BIN) and os.access(GATEKEEPER_BIN, os.X_OK)
    if has_gatekeeper:
        gate = subprocess.run(
            [GATEKEEPER_BIN, "acquire", cleaned_agent, "120000"],
            capture_output=True,
            text=True,
        )
        if gate.returncode != 0:
            print(
                f"[MEDIA_MONITOR_ERROR] Gatekeeper acquisition failed: {gate.stderr.strip()}",
                file=sys.stderr,
            )
            return

    try:
        turns = []
        try:
            turns = parse_turn_script_payload(cleaned_text)
        except (OSError, json.JSONDecodeError) as error:
            print(f"[MEDIA_MONITOR_ERROR] Turn script parse failure: {error}", file=sys.stderr)
            return

        if not turns and cleaned_text and not is_placeholder(cleaned_text):
            turns = [{"agent": cleaned_agent, "text": cleaned_text}]

        turns = enforce_minimum_council(turns, cleaned_agent)
        turns = [turn for turn in turns if sanitize_input(turn.get("text", ""))]
        if not turns:
            print("[MEDIA_MONITOR_ERROR] No valid non-placeholder speech content to dispatch.", file=sys.stderr)
            return

        ui_path = str(SSOT_ROOT / "ops" / "scripts" / "fullscreen_ui")
        if ui_path not in sys.path:
            sys.path.insert(0, ui_path)

        dispatched_stage = False
        try:
            from sync_stage_engine import play_script_pipelined, speak_with_word_sync
            if len(turns) > 1:
                play_script_pipelined(turns, gap_seconds=0.35)
            else:
                spk = turns[0].get("agent", cleaned_agent).lower()
                utt = turns[0].get("text", "")
                if utt:
                    speak_with_word_sync(spk, utt)
            dispatched_stage = True
        except Exception as stage_err:
            # Fallback for Windows SAPI when Kokoro/afplay is macOS-specific
            if sys.platform == "win32":
                try:
                    import win32com.client
                    speaker = win32com.client.Dispatch("SAPI.SpVoice")
                    speaker.Rate = -1
                    speaker.Volume = 100
                    for t in turns:
                        spk = t.get("agent", cleaned_agent)
                        utt = t.get("text", "")
                        if utt:
                            speaker.Speak(f"{spk}: {utt}")
                    dispatched_stage = True
                except Exception as sapi_err:
                    print(f"[MEDIA_MONITOR_WARN] Windows SAPI fallback failed: {sapi_err}", file=sys.stderr)

        time.sleep(0.05)
    finally:
        if has_gatekeeper:
            subprocess.run(
                [GATEKEEPER_BIN, "release"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                check=False,
            )


if __name__ == "__main__":
    ag = sys.argv[1] if len(sys.argv) > 1 else "maxx"
    tx = sys.argv[2] if len(sys.argv) > 2 else ""
    run_isolated_stream(ag, tx)
