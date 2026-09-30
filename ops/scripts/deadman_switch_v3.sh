#!/usr/bin/env bash
# =============================================================================
# XORAS DEAD MAN'S SWITCH V3 (100% PURE BASH REAL ELAPSED TIME ENFORCER)
# Anchors timer to start of active execution and measures real elapsed seconds.
# If silence between active dispatches > MAX_SILENCE_SECONDS, boot sequence
# is ABORTED instantly with Exit Code 1.
# =============================================================================
set -euo pipefail

MAX_SILENCE_SECONDS="${1:-15}"
START_TS_FILE="/tmp/xoras_quorum_start_timestamp.txt"
SPEECH_TS_FILE="/tmp/xoras_last_speech_timestamp.txt"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPEAK_SCRIPT="${SCRIPT_DIR}/agent_speak.sh"

NOW="$(date +%s)"

# 1. Read or initialize start timestamp
if [[ -f "$START_TS_FILE" ]]; then
  START_TS="$(cat "$START_TS_FILE" 2>/dev/null || echo "$NOW")"
else
  START_TS="$NOW"
  echo "$START_TS" > "$START_TS_FILE"
fi

# 2. Read last speech timestamp
if [[ -f "$SPEECH_TS_FILE" ]]; then
  SPEECH_TS="$(cat "$SPEECH_TS_FILE" 2>/dev/null || echo "$NOW")"
else
  SPEECH_TS="$START_TS"
fi

# Calculate real elapsed time since last spoken beat
ELAPSED=$((NOW - SPEECH_TS))
TOTAL_RUN=$((NOW - START_TS))

if (( ELAPSED > MAX_SILENCE_SECONDS )); then
  echo "🚨 [DEAD MAN SWITCH V3] HARD ABORT: Silence timeout violation! ${ELAPSED}s elapsed since last speech beat (Max limit: ${MAX_SILENCE_SECONDS}s)." >&2
  echo "   [TOTAL RUN TIME]: ${TOTAL_RUN}s | [STATUS]: ABORTING BOOT SEQUENCE." >&2
  
  # Trigger forced audio explanation before halting
  bash "$SPEAK_SCRIPT" "jarvis" "Jarvis alert. Dead man switch triggered. Silence violation detected. Boot sequence aborted."
  
  exit 1
fi

echo "🟢 [DEAD MAN SWITCH V3] Real elapsed speech heartbeat: ${ELAPSED}s since last beat (Limit: ${MAX_SILENCE_SECONDS}s | Run: ${TOTAL_RUN}s)."
