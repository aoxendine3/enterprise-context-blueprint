#!/usr/bin/env bash
# Single-command outsider reproducer: Reality Gate (9/9) + Blackboard/MCP Head-to-Head + Fuzz/Unit Suites.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd -P)"
cd "$ROOT"

echo "[1/3] Running fail-closed Reality Gate (9/9)..."
bash ops/scripts/reality_gate.sh

echo "[2/3] Running identical-workload Blackboard + MCP head-to-head..."
python3 core/ops/benchmarks/blackboard_mcp_head_to_head.py

echo "[3/3] Running head-to-head, memory, fuzz, Windows client, and voice suites..."
python3 -m pytest -q \
  tests/test_blackboard_mcp_head_to_head.py \
  tests/test_retain_recall.py \
  tests/test_retain_recall_fuzz.py \
  tests/test_windows_sovereign_client.py \
  tests/test_collective_report_voice.py \
  tests/test_upstream_claim_gate.py

echo "REPRODUCE_ALL_PASS: Reality Gate (9/9), Blackboard+MCP head-to-head, and all targeted suites verified."
