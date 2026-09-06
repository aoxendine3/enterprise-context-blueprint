#!/usr/bin/env bash
# monitor_health.sh – validates communication daemons without injecting placeholder speech
set -euo pipefail

LOG="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/reports/monitor_daemon.log"
VOICE_DAEMON="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/voice_daemon.py"
COMMS_PIPELINE="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/agent_comms_pipeline.py"

mkdir -p "$(dirname "$LOG")"

ensure_running() {
  local label="$1"
  local match="$2"
  shift 2
  if pgrep -f "$match" >/dev/null 2>&1; then
    echo "$(date) – ${label} alive" >> "$LOG"
    return
  fi
  echo "$(date) – ${label} missing, restarting" >> "$LOG"
  nohup "$@" >> "$LOG" 2>&1 &
  sleep 1
  if pgrep -f "$match" >/dev/null 2>&1; then
    echo "$(date) – ${label} restart success" >> "$LOG"
  else
    echo "$(date) – ${label} restart failed" >> "$LOG"
  fi
}

ensure_running "voice_daemon" "ops/scripts/voice_daemon.py" python3 -u "$VOICE_DAEMON"
ensure_running "agent_comms_pipeline" "ops/scripts/agent_comms_pipeline.py" python3 -u "$COMMS_PIPELINE"

IMG_FILE="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/current_image.txt"
if [[ -f "$IMG_FILE" ]]; then
  MOD=$(stat -f "%m" "$IMG_FILE")
  NOW=$(date +%s)
  if (( NOW - MOD > 60 )); then
    echo "$(date) – Idle detected on stage state file (no synthetic speech injected)" >> "$LOG"
  fi
fi
