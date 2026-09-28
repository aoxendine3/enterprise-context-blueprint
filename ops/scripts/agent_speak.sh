#!/usr/bin/env bash
# =============================================================================
# XORAS SYSTEM: CANONICAL AGENT SPEAK DISPATCHER
# Native Zig Binary. Zero Python. Zero middle layers.
# Direct bare-metal audio synthesis and 3D stage sync.
# =============================================================================
set -euo pipefail

AGENT="${1:-maxx}"
RAW_TEXT="${2:-}"

BIN="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/bin/xoras_speak"

if [[ -z "${RAW_TEXT//[[:space:]]/}" ]]; then
  echo "[agent_speak] refused empty speech payload" >&2
  exit 2
fi

exec "$BIN" "$AGENT" "$RAW_TEXT"
