#!/usr/bin/env bash
# =============================================================================
# XORAS TRINITY EXECUTION WRAPPER
# Order of Execution:
# 1. Per-Turn Guard check (ops/scripts/per_turn_guard.py)
# 2. Trinity Gate consensus (ops/discernment/merkle_pre_action_gate.py)
# 3. Target Command Execution
# =============================================================================
set -euo pipefail

SSOT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "=== STEP 1: PER-TURN 7TH-LAYER GUARD CHECK ==="
if ! python3 "${SSOT_ROOT}/ops/scripts/per_turn_guard.py"; then
  echo "[run_with_trinity] ABORT: Per-turn guard check failed." >&2
  exit 1
fi

echo "=== STEP 2: TRINITY GATE CONSENSUS ==="
if ! python3 "${SSOT_ROOT}/ops/discernment/merkle_pre_action_gate.py"; then
  echo "[run_with_trinity] ABORT: Trinity pre-action gate failed." >&2
  exit 2
fi

echo "=== STEP 3: EXECUTING TARGET COMMAND ==="
exec "$@"
