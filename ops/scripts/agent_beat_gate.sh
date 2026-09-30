#!/usr/bin/env bash
# =============================================================================
# XORAS HARD RUNTIME SPEECH BEAT GATE (100% PURE BASH BINDING LAW)
# If speech fails or is skipped, execution HALTS instantly.
# =============================================================================
set -euo pipefail

AGENT="${1:-maxx}"
BEAT_TYPE="${2:-STATUS}"
MESSAGE="${3:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPEAK_SCRIPT="${SCRIPT_DIR}/agent_speak.sh"

if [[ -z "${MESSAGE//[[:space:]]/}" ]]; then
  echo "[agent_beat_gate] FATAL: Refused empty speech payload for beat ${BEAT_TYPE}" >&2
  exit 1
fi

BEAT_UPPER="$(echo "$BEAT_TYPE" | tr '[:lower:]' '[:upper:]')"
case "$BEAT_UPPER" in
  INTENT|STATUS|RESULT|TRANSITION)
    ;;
  *)
    BEAT_UPPER="STATUS"
    ;;
esac

AGENT_UPPER="$(echo "$AGENT" | tr '[:lower:]' '[:upper:]')"
echo "🔊 [${BEAT_UPPER}] [${AGENT_UPPER}]: ${MESSAGE}"

if [[ ! -x "$SPEAK_SCRIPT" ]]; then
  chmod +x "$SPEAK_SCRIPT"
fi

# Atomic commit of spoken beat into the cryptographic Merkle Catch DAG tree
python3 "${SCRIPT_DIR}/merkle_catch_dag.py" commit "$AGENT" "$BEAT_UPPER" "$MESSAGE" 2>/dev/null || true

# Hard Runtime Gate: Execute pure Bash audio dispatch. Halt if non-zero return.
if ! bash "$SPEAK_SCRIPT" "$AGENT" "${MESSAGE}"; then
  echo "[agent_beat_gate] FATAL: Speech beat ${BEAT_UPPER} for ${AGENT} failed. Runtime halting." >&2
  exit 1
fi
