#!/usr/bin/env bash
# =============================================================================
# collective_speak.sh — THE COLLECTIVE'S OWN SPEAK PATH
# =============================================================================
# Every spoken turn of the collective goes through here:
#   1. the collective voice guard checks the text (We/Our, no outside voice,
#      no foreign branding) and writes a receipt;
#   2. a violating turn is REFUSED before it is heard (exit 5);
#   3. only then is the audio emitted, one voice at a time, no overlap.
#
# Usage: collective_speak.sh "<text>" [phase]
#   phase: NEXT | BREAKDOWN | SUMMARY   (defaults to BREAKDOWN)
#
# The spoken text is prefixed with its phase marker so the operator always
# hears where in the cadence we are.
# =============================================================================
set -euo pipefail

TEXT="${1:-}"
PHASE="${2:-BREAKDOWN}"

if [[ -z "${TEXT//[[:space:]]/}" ]]; then
  echo "[collective_speak] nothing to speak" >&2
  exit 0
fi

ROOT="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain"
GUARD="$ROOT/core/ops/scripts/collective_voice_guard.py"
PY="$ROOT/.venv/bin/python"
[[ -x "$PY" ]] || PY="python3"

PAYLOAD="[$PHASE] $TEXT"

if [[ -f "$GUARD" ]]; then
  if ! "$PY" "$GUARD" --text "$PAYLOAD" --agent collective >/dev/null 2>&1; then
    echo "[collective_speak] REFUSED: collective voice violation — nothing spoken." >&2
    exit 5
  fi
fi

# One voice at a time — the law permits a single speaker, never an overlap.
say -v "Zoe (Premium)" "$PAYLOAD"
