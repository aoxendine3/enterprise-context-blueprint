#!/usr/bin/env bash
# =============================================================================
# TRINITY GATE WRAPPER — dispatch → independent verify → execute on pass
# Governance: AGENTS.md Trinity Gate (Layer 7), Log Entry #078.
# Flow:  1. Dispatch three distinct real audio briefings (Maxx, Clara, Vance)
#        2. Independent BFT verifier (trinity_gate.py) enforces 2-of-3 quorum
#        3. On PASS: execute the requested command
#           On FAIL: fail closed, log to memory/catch_log/trinity_gate.log
# =============================================================================
set -euo pipefail
unset DYLD_INSERT_LIBRARIES DYLD_LIBRARY_PATH LD_PRELOAD LD_LIBRARY_PATH 2>/dev/null || true

ROOT="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain"
PY="$ROOT/.venv/bin/python"
[[ -x "$PY" ]] || PY="python3"

DISPATCH="$ROOT/core/ops/scripts/trinity_dispatch.py"
GATE="$ROOT/core/ops/scripts/trinity_gate.py"
POLICY_ENGINE="$ROOT/ops/scripts/sovereign_policy_engine.py"

if [[ $# -eq 0 ]]; then
  echo "usage: run_with_trinity.sh <command> [args...]" >&2
  exit 2
fi

CMD_STR="$*"

# STAGE 0: Policy Engine (Intent Filter) — advisory; never blocks dispatch
if [[ -f "$POLICY_ENGINE" ]]; then
  python3 "$POLICY_ENGINE" "$@" >/dev/null 2>&1 || true
fi

# STAGE 1: Dispatch three distinct real audio briefings for THIS command
"$PY" "$DISPATCH" --command "$CMD_STR" >/dev/null || {
  echo "❌ TRINITY FAIL-CLOSED: audio briefing dispatch incomplete — no quorum attempt, nothing executed."
  exit 1
}

# STAGE 2: Independent BFT verifier (2-of-3 distinct approved agents)
TRINITY_OUTPUT=$("$PY" "$GATE" 2>/dev/null) || {
  echo "❌ TRINITY GATE FAILED CLOSED: quorum not achieved."
  echo "$TRINITY_OUTPUT"
  exit 1
}

PASSED=$(echo "$TRINITY_OUTPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('passed', False))" 2>/dev/null || echo "False")
APPROVED=$(echo "$TRINITY_OUTPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('approved_count', 0))" 2>/dev/null || echo "0")

if [[ "$PASSED" == "True" ]] && [[ "$APPROVED" -ge 2 ]]; then
  echo "✅ TRINITY GATE PASSED: $APPROVED distinct approved agent briefings. Executing command."
  exec "$@"
else
  echo "❌ TRINITY GATE FAILED CLOSED: quorum not achieved (Approved: $APPROVED/3)."
  exit 1
fi
