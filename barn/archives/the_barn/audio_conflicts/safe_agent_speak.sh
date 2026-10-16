#!/bin/bash
# Fixed Audio Engine — Zero Mutation, Exact Git Manifest Reader
AGENT="$1"
TEXT="$2"

LOCKDIR="/tmp/sovereign_audio_speaker.lock"
while ! mkdir "$LOCKDIR" 2>/dev/null; do
    sleep 0.2
done
trap 'rm -rf "$LOCKDIR"' EXIT

# QUARANTINE STUB: Legacy script disabled. Use core/ops/scripts/agent_speak.sh instead.
echo "[ERROR] safe_agent_speak.sh is deprecated and quarantined. Please use the canonical agent_speak.sh script."
exit 1
