#!/bin/bash
# Fixed Audio Engine — Zero Mutation, Exact Git Manifest Reader
AGENT="$1"
TEXT="$2"

LOCKDIR="/tmp/sovereign_audio_speaker.lock"
while ! mkdir "$LOCKDIR" 2>/dev/null; do
    sleep 0.2
done
trap 'rm -rf "$LOCKDIR"' EXIT

python3 /Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/sync_stage_engine_kokoro.py "$AGENT" "$TEXT"
