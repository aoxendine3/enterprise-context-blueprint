#!/usr/bin/env bash
# =============================================================================
# XORAS SYSTEM: CANONICAL AGENT SPEAK DISPATCHER (100% PURE BASH)
# Zero Python. Zero middle layers. Direct bare-metal audio synthesis.
# =============================================================================
set -euo pipefail

AGENT="${1:-maxx}"
RAW_TEXT="${2:-}"

if [[ -z "${RAW_TEXT//[[:space:]]/}" ]]; then
  echo "[agent_speak] Refused empty speech payload" >&2
  exit 2
fi

VOICE="Jamie (Premium)"

case "$AGENT" in
  maxx|bm_george)
    VOICE="Evan (Enhanced)"
    ;;
  jarvis|am_adam)
    VOICE="Jamie (Premium)"
    ;;
  daxx)
    VOICE="Lee (Premium)"
    ;;
  clara|af_sarah)
    VOICE="Zoe (Premium)"
    ;;
  vance|am_michael)
    VOICE="Nathan (Enhanced)"
    ;;
  jeremy|dr_jeremy)
    VOICE="Oliver (Enhanced)"
    ;;
  eden|dr_eden)
    VOICE="Ava (Enhanced)"
    ;;
  evan)
    VOICE="Tom (Enhanced)"
    ;;
  aurelius)
    VOICE="Rishi (Enhanced)"
    ;;
  john)
    VOICE="Daniel (Enhanced)"
    ;;
  selene)
    VOICE="Joelle (Enhanced)"
    ;;
  orion)
    VOICE="Matilda (Premium)"
    ;;
  *)
    VOICE="Jamie (Premium)"
    ;;
esac

# Pure Bash File Mutex Lock & Native macOS Speech Execution
LOCKDIR="/tmp/coreaudio_single_speaker.lockdir"

# Stale lock cleanup (if lock is older than 5 seconds)
if [[ -d "$LOCKDIR" ]]; then
  NOW_SEC=$(date +%s)
  MOD_SEC=$(stat -f %m "$LOCKDIR" 2>/dev/null || echo 0)
  LOCK_AGE=$((NOW_SEC - MOD_SEC))
  if [ "$LOCK_AGE" -gt 5 ]; then
    rm -rf "$LOCKDIR" 2>/dev/null || true
  fi
fi

while ! mkdir "$LOCKDIR" 2>/dev/null; do
  sleep 0.05
done

# Ensure lock cleanup on exit or error
trap 'rm -rf "$LOCKDIR"' EXIT INT TERM

# Direct Bare-Metal Audio Playback (Synchronous real-time audio output)
CLEAN_TEXT="$(echo "$RAW_TEXT" | tr -d '"')"
NORMALIZER="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/bin/speech_normalizer"
if [[ -x "$NORMALIZER" ]]; then
  CLEAN_TEXT="$("$NORMALIZER" "$CLEAN_TEXT")"
fi

# Daxx voice lock: Lee (Premium) is Anthony's explicit choice in ELITE_BOW card
if [[ "$AGENT" == "daxx" ]]; then
  echo "daxx" > /Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/current_image.txt 2>/dev/null || true
  echo "$CLEAN_TEXT" > /Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/current_transcript.txt 2>/dev/null || true
  say -v "$VOICE" "$CLEAN_TEXT"
else
  # Kokoro-first: all other agents use neural synthesis. macOS say is emergency fallback only.
  KOKORO_SCRIPT="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/sync_stage_engine_kokoro.py"
  if python3 "$KOKORO_SCRIPT" "$AGENT" "$CLEAN_TEXT" 2>/dev/null; then
    : # Kokoro succeeded
  else
    # Fallback to macOS say only if Kokoro fails
    say -v "$VOICE" "$CLEAN_TEXT"
  fi
fi

# Update Dead Man Switch timestamp receipt
date +%s > /tmp/xoras_last_speech_timestamp.txt

# Storage protection: auto-prune temporary wav/aiff audio files and old voice cache
rm -f /tmp/*.wav /tmp/*.aiff /tmp/live_speech.wav 2>/dev/null || true
find ~/.sovereign/voice_cache/ -type f -mmin +10 -delete 2>/dev/null || true
