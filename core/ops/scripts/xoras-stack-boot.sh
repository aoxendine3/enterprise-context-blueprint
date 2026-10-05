#!/usr/bin/env bash
# xoras-stack-boot.sh — Boot full Xoras stack end-to-end
# Usage: bash ops/scripts/xoras-stack-boot.sh
set -euo pipefail

export XORAS_ROOT="${XORAS_ROOT:-$HOME/Desktop/Xoras_Workspace}"
export XORAS_PROJECT="${XORAS_PROJECT:-$XORAS_ROOT/AI_Core/Xoras_Project}"
export XORAS_SOURCE="${XORAS_SOURCE:-$XORAS_PROJECT/xoras-core/Source}"
export XORAS_PERSONA_API="${XORAS_PERSONA_API:-http://127.0.0.1:8787}"

echo "=== XORAS FULL STACK BOOT ==="
echo "Project: $XORAS_PROJECT"
echo "Source:  $XORAS_SOURCE"
echo ""

if [[ ! -d "$XORAS_SOURCE" ]]; then
  echo "ERROR: Source not found at $XORAS_SOURCE"
  exit 1
fi

cd "$XORAS_SOURCE"

# 1. Wake sequence (identity, memory, security, services, health gates)
echo "[1/3] Running wake sequence..."
python3 xoras_wake.py || {
  echo "WARN: Wake sequence reported failure — check xoras_startup.log"
}

# 2. Sovereign awaken (background, optional — hippocampus consolidation)
SOVEREIGN_BIN="${SOVEREIGN_BIN:-$HOME/.sovereign/venv/bin/sovereign}"
if [[ -x "$SOVEREIGN_BIN" ]]; then
  echo "[2/3] Sovereign stack available at $SOVEREIGN_BIN"
  echo "      Run manually for continuous existence: sovereign awaken"
else
  echo "[2/3] Sovereign CLI not found — skipping (dream orchestrator handles consolidation)"
fi

# 3. Status summary
echo "[3/3] Stack status"
bash "$XORAS_ROOT/ops/scripts/wake-status.sh" 2>/dev/null || true

if curl -sf "${XORAS_PERSONA_API}/health" >/dev/null 2>&1; then
  echo "Persona API:  ONLINE ($XORAS_PERSONA_API)"
else
  echo "Persona API:  OFFLINE — start with: cd $XORAS_SOURCE && python3 xoras_persona_api.py"
fi

if [[ -f "$XORAS_SOURCE/.xoras_stack_status.json" ]]; then
  echo "Supervisor:   $(python3 -c "import json; d=json.load(open('$XORAS_SOURCE/.xoras_stack_status.json')); print(d)" 2>/dev/null || echo 'see .xoras_stack_status.json')"
fi

echo ""
echo "Desktop app:  cd $XORAS_PROJECT/xoras-app && npm run tauri dev"
echo "Stack boot complete."
