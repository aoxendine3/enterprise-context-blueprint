#!/usr/bin/env bash
# =============================================================================
# SOVEREIGN AGENTIC APP: CANONICAL LOCAL AUDIO SPEECH DISPATCHER
# Workspace: labs/workspaces/sovereign-agentic-app
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PYTHON_EXEC="$APP_ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON_EXEC" ]]; then
  PYTHON_EXEC="python3"
fi

exec "$PYTHON_EXEC" "$SCRIPT_DIR/speak.py" "$@"
