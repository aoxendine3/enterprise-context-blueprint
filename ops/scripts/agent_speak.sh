#!/usr/bin/env bash
# =============================================================================
# XORAS SYSTEM: CANONICAL AGENT SPEAK DISPATCHER
# Invariant: Hand off DIRECTLY to the Media Stream Monitor.
# The Monitor IS the Director. Zero extra middlemen.
# =============================================================================
set -euo pipefail

AGENT="${1:-maxx}"
RAW_TEXT="${2:-Operational on metal.}"

DIRECTOR="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/media_director_agent.py"

# Hand off exclusively to the Sovereign Media Director Agent (Log Entry #065)
python3 "$DIRECTOR" "$AGENT" "$RAW_TEXT"
