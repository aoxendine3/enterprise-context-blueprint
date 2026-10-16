#!/usr/bin/env bash
# =============================================================================
# XORAS SYSTEM: CANONICAL AGENT SPEAK DISPATCHER (100% KOKORO HARDWARE LOCK)
# Mandatory 7th-Layer Kokoro Hardware Lock. Zero macOS say. Zero fallbacks.
# =============================================================================
set -euo pipefail

AGENT="${1:-maxx}"
RAW_TEXT="${2:-}"

# 1. Enforce strict Agent identity allowlist
if [[ ! "$AGENT" =~ ^(maxx|clara|jarvis|vance|daxx|john|eden|selene|sophia|xoras|aurelius)$ ]]; then
  echo "[agent_speak] FATAL: Forged or unauthorized agent identity '$AGENT'. Execution denied." >&2
  exit 3
fi

# 2. Reject empty payload
if [[ -z "${RAW_TEXT//[[:space:]]/}" ]]; then
  echo "[agent_speak] Refused empty speech payload" >&2
  exit 2
fi

# 3. Length-cap the message text (Max 1000 chars)
if [[ ${#RAW_TEXT} -gt 1000 ]]; then
  echo "[agent_speak] FATAL: Payload exceeds 1000 character limit. Execution denied." >&2
  exit 4
fi

# 4. Strip dangerous shell metacharacters to prevent command injection
# Removes: $, ;, |, &, >, <, `, (, )
RAW_TEXT=$(echo "$RAW_TEXT" | tr -d '$;|&><`()')

LOCKFILE="/tmp/coreaudio_single_speaker.lock"
exec 9> "$LOCKFILE"
# Block until lock is acquired, OS automatically releases it when process exits
perl -e 'use Fcntl qw(:flock); flock(STDIN, LOCK_EX) or die "Lock failed";' <&9

CLEAN_TEXT="$(echo "$RAW_TEXT" | tr -d '"')"
NORMALIZER="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/bin/speech_normalizer"
if [[ -x "$NORMALIZER" ]]; then
  CLEAN_TEXT="$("$NORMALIZER" "$CLEAN_TEXT")"
fi

KOKORO_SCRIPT="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/sync_stage_engine_kokoro.py"

echo "$AGENT" > /Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/current_image.txt 2>/dev/null || true
echo "$CLEAN_TEXT" > /Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/current_transcript.txt 2>/dev/null || true

PYTHON_EXEC="python3"
if [[ -x "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/.venv/bin/python" ]]; then
  PYTHON_EXEC="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/.venv/bin/python"
fi

if ! "$PYTHON_EXEC" "$KOKORO_SCRIPT" "$AGENT" "$CLEAN_TEXT"; then
  echo "[agent_speak ERROR] Kokoro neural synthesis failed for agent '$AGENT'. Fallbacks forbidden." >&2
  exit 1
fi

date +%s > /tmp/xoras_last_speech_timestamp.txt
rm -f /tmp/*.wav /tmp/*.aiff /tmp/live_speech.wav 2>/dev/null || true
