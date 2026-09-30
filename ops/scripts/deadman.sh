#!/usr/bin/env bash
# =============================================================================
# XORAS DEADMAN SILENCE MONITOR (100% PURE BASH)
# Real elapsed-time wall-clock silence monitor reading /tmp/quorum_activity.log
# Executes hard process kill on silence exceeding 15 seconds.
# =============================================================================
set -euo pipefail

MAX_SILENCE_SECONDS="${1:-15}"
LOG_FILE="/tmp/quorum_activity.log"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPEAK_SCRIPT="${SCRIPT_DIR}/agent_speak.sh"

NOW="$(date +%s)"

if [[ ! -f "$LOG_FILE" ]]; then
  echo "🚨 [DEADMAN SILENCE MONITOR] HARD ABORT: Log file '${LOG_FILE}' does not exist!" >&2
  pkill -9 -f "quorum_router.sh" 2>/dev/null || true
  exit 1
fi

# Extract last Unix timestamp from log file (first token of line) or stat modtime
LAST_TS=""
if [[ -s "$LOG_FILE" ]]; then
  LAST_TS=$(grep -E '^[0-9]{10}' "$LOG_FILE" 2>/dev/null | tail -n 1 | awk '{print $1}' || echo "")
fi

if [[ -z "$LAST_TS" ]]; then
  LAST_TS=$(stat -f %m "$LOG_FILE" 2>/dev/null || echo "")
fi

if [[ -z "$LAST_TS" ]]; then
  LAST_TS=0
fi

ELAPSED=$((NOW - LAST_TS))

if (( ELAPSED > MAX_SILENCE_SECONDS )); then
  echo "🚨 [DEADMAN SILENCE MONITOR] HARD ABORT: Silence timeout violation! ${ELAPSED}s elapsed since last activity in ${LOG_FILE} (Max limit: ${MAX_SILENCE_SECONDS}s)." >&2
  
  # Hard process kill on quorum router processes
  echo "   [ACTION]: Executing hard process kill on quorum router..." >&2
  pkill -9 -f "quorum_router.sh" 2>/dev/null || true

  # Audio alert if speak script available
  if [[ -f "$SPEAK_SCRIPT" ]]; then
    bash "$SPEAK_SCRIPT" "jarvis" "Jarvis alert. Deadman switch triggered. Quorum silence exceeded 15 seconds. Hard process kill executed." || true
  fi

  exit 1
fi

echo "🟢 [DEADMAN SILENCE MONITOR] Silence check PASSED: ${ELAPSED}s since last activity in ${LOG_FILE} (Limit: ${MAX_SILENCE_SECONDS}s)."
exit 0
