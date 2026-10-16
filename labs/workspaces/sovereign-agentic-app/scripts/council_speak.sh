#!/usr/bin/env bash
# =============================================================================
# Sovereign Agentic App — Frozen Council Audio Dispatch Wrapper
# Canonical Zero-Gap Live Dispatcher for Lead 9 Council & R&D
# Substrate: Apple Silicon M4 Unified RAM (Kokoro ONNX)
# Gap: 0.40s natural breath between speakers
# =============================================================================

set -euo pipefail

PYTHON_EXEC="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/.venv/bin/python"
DISPATCH_SCRIPT="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/council_audio_dispatch.py"

if [ ! -f "$PYTHON_EXEC" ] || [ ! -f "$DISPATCH_SCRIPT" ]; then
    echo "❌ Error: Python venv or council_audio_dispatch.py not found" >&2
    exit 1
fi

if [ -t 0 ]; then
    # Terminal input without pipe/redirect
    if [ "$#" -eq 0 ]; then
        echo "Usage: $0 --json < payload.json"
        echo "   or: $0 '[[\"maxx\", \"text\"], [\"clara\", \"text\"], [\"vance\", \"text\"]]'"
        exit 1
    fi
    exec "$PYTHON_EXEC" "$DISPATCH_SCRIPT" --json <<< "$1"
else
    # Piped input from stdin
    exec "$PYTHON_EXEC" "$DISPATCH_SCRIPT" --json
fi
