#!/bin/bash
# Direct Audio Dispatch via Kokoro Neural Engine
AGENT="$1"
TEXT="$2"

LOCKDIR="/tmp/kokoro_direct_audio.lock"
while ! mkdir "$LOCKDIR" 2>/dev/null; do
    sleep 0.2
done
trap 'rm -rf "$LOCKDIR"' EXIT

python3 /Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/sync_stage_engine_kokoro.py "$AGENT" "$TEXT"
