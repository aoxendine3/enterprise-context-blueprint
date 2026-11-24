#!/usr/bin/env bash
# =============================================================================
# XORAS SYSTEM: CANONICAL AGENT SPEAK DISPATCHER (100% KOKORO HARDWARE LOCK)
# Mandatory 7th-Layer Kokoro Hardware Lock. Zero macOS say. Zero fallbacks.
# =============================================================================
set -euo pipefail

AGENT="${1:-maxx}"
RAW_TEXT="${2:-}"

# Resolve the checkout from this script (physical path, so the ops/ symlink is
# harmless). No personal absolute path: the wake path works from any clone.
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT="$(cd "$SCRIPTS_DIR/../../.." && pwd)"

# 1. Enforce strict Agent identity allowlist
if [[ ! "$AGENT" =~ ^(maxx|clara|jarvis|vance|daxx|john|eden|selene|sophia|xoras|aurelius)$ ]]; then
  echo "[agent_speak] FATAL: Forged or unauthorized agent identity '$AGENT'. Execution denied." >&2
  exit 3
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
NORMALIZER="$ROOT/ops/bin/speech_normalizer"
if [[ -x "$NORMALIZER" ]]; then
  CLEAN_TEXT="$("$NORMALIZER" "$CLEAN_TEXT")"
fi

# 2. Reject empty payload after sanitization
if [[ -z "${CLEAN_TEXT//[[:space:]]/}" ]]; then
  echo "[agent_speak] Refused empty speech payload after sanitization" >&2
  exit 0
fi

# 4. Length-cap the message text (Max 1000 chars)
if [[ ${#CLEAN_TEXT} -gt 1000 ]]; then
  echo "[agent_speak] FATAL: Payload exceeds 1000 character limit. Execution denied." >&2
  exit 4
fi

KOKORO_SCRIPT="$ROOT/ops/scripts/fullscreen_ui/sync_stage_engine_kokoro.py"

echo "$AGENT" > "$ROOT/ops/scripts/fullscreen_ui/current_image.txt" 2>/dev/null || true
echo "$CLEAN_TEXT" > "$ROOT/ops/scripts/fullscreen_ui/current_transcript.txt" 2>/dev/null || true

PYTHON_EXEC="python3"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON_EXEC="$ROOT/.venv/bin/python"
fi

# 5. Collective voice enforcement (absolute rule). We speak as the collective
#    (We / Our). A turn that speaks as an outside assistant, or that carries
#    foreign product branding, is refused before it can be heard.
VOICE_GUARD="$ROOT/ops/scripts/collective_voice_guard.py"
if [[ -f "$VOICE_GUARD" ]]; then
  if ! "$PYTHON_EXEC" "$VOICE_GUARD" --text "$CLEAN_TEXT" --agent "$AGENT" >/dev/null 2>&1; then
    echo "[agent_speak] REFUSED: collective voice violation — this turn is not the collective's voice. Nothing spoken." >&2
    exit 5
  fi
fi

if ! "$PYTHON_EXEC" "$KOKORO_SCRIPT" "$AGENT" "$CLEAN_TEXT"; then
  echo "[agent_speak ERROR] Kokoro neural synthesis failed for agent '$AGENT'. Fallbacks forbidden." >&2
  exit 1
fi

date +%s > /tmp/xoras_last_speech_timestamp.txt
rm -f /tmp/*.wav /tmp/*.aiff /tmp/live_speech.wav 2>/dev/null || true
