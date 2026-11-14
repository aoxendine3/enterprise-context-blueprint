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
  # --require-plan enforces the TURN NARRATION CONTRACT: the turn must open
  # with its phase, and must state what happens next (and, for a breakdown,
  # what was actually done). A turn that cannot say those is not permitted
  # to be heard — the operator is never left guessing.
  if ! "$PY" "$GUARD" --text "$PAYLOAD" --agent collective --require-plan >/dev/null 2>&1; then
    echo "[collective_speak] REFUSED: collective voice or narration contract violation — nothing spoken." >&2
    exit 5
  fi
fi

# Record the turn so the operator can always ask what any agent is doing.
TURN_LEDGER="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/core/ops/scripts/turn_ledger.py"
if [[ -f "$TURN_LEDGER" ]]; then
  "$PY" "$TURN_LEDGER" --agent "${COLLECTIVE_SPEAKER:-collective}" --phase "$PHASE" --text "$TEXT" >/dev/null 2>&1 || true
fi

# One voice at a time — the law permits a single speaker, never an overlap.
# If another collective turn is already speaking, this one WAITS for the
# stage to clear rather than talking over it.
# NOTE: macOS has no flock(1); the repo's canonical lock is the perl
# Fcntl::flock pattern (same as ops/scripts/agent_speak.sh). The perl child
# exits immediately, but the lock is held on the SHARED open file description,
# so the stage stays locked for as long as this shell holds fd 8.
VOICE_LOCK="/tmp/xoras_collective_voice.lock"
exec 8>"$VOICE_LOCK"
if ! perl -e 'use Fcntl qw(:flock); $SIG{ALRM}=sub{exit 1}; alarm(300); flock(STDIN, LOCK_EX) or exit 1;' <&8; then
  echo "[collective_speak] stage busy — turn deferred, nothing spoken." >&2
  exit 6
fi

say -v "Zoe (Premium)" "$PAYLOAD"
