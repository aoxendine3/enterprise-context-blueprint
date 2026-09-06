#!/usr/bin/env bash
# =============================================================================
# XORAS SYSTEM: CANONICAL AGENT SPEAK DISPATCHER
# Invariant: Hand off DIRECTLY to the Media Stream Monitor.
# The Monitor IS the Director. Zero extra middlemen.
# =============================================================================
set -euo pipefail

AGENT="${1:-maxx}"
RAW_TEXT="${2:-}"

DIRECTOR="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/media_director_agent.py"

if [[ -z "${RAW_TEXT//[[:space:]]/}" ]]; then
  echo "[agent_speak] refused empty speech payload" >&2
  exit 2
fi

# Hand off exclusively to the Sovereign Media Director Agent (Log Entry #065)
python3 "$DIRECTOR" "$AGENT" "$RAW_TEXT"
