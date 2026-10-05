#!/usr/bin/env bash
# =============================================================================
# XORAS TURN-KEY ENTERPRISE BOOT ENGINE (100% PURE BASH BINDING LAW)
# Single Command Turn-Key Enterprise Stack Deployment:
#   1. Port 8080 Sovereign Stage & Telemetry Daemon
#   2. Pre-Deliberation Health Gate V2 (SHA-256 Digests + Local Probes)
#   3. Merkle Catch DAG Tree Commitment ($R_tree Root Hash)
#   4. 3-Agent Quorum Spoken Audio Deliberation (Maxx, Vance, Dr. Eden)
#   5. Voice Dead Man's Switch Heartbeat Verification
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${SCRIPT_DIR}/.."
PYTHON_BIN="$(which python3)"

echo "================================================================="
echo "XORAS TURN-KEY ENTERPRISE SYSTEM BOOT (100% OFF-GRID LAW)"
echo "================================================================="

# Step 1: Ensure Port 8080 Stage HTTP & Telemetry Server
echo "[STEP 1/5] Verifying Sovereign Stage Server (Port 8080)..."
if ! curl -s -f "http://127.0.0.1:8080/customer_app.html" >/dev/null 2>&1; then
  echo "[*] Port 8080 dark. Auto-spawning Sovereign Stage daemon..."
  "$PYTHON_BIN" "${SCRIPT_DIR}/fullscreen_server.py" >/dev/null 2>&1 &
  sleep 1.5
fi
curl -s -f "http://127.0.0.1:8080/customer_app.html" >/dev/null 2>&1
echo "🟢 [STAGE PORT 8080] ONLINE & VERIFIED (http://127.0.0.1:8080/customer_app.html)"

# Step 2: Run Pre-Deliberation Health Gate V2
echo ""
echo "[STEP 2/5] Executing Pre-Deliberation Health Gate V2..."
"$PYTHON_BIN" "${SCRIPT_DIR}/preflight_health_gate.py"

# Step 3: Merkle Catch DAG Commitment & Root Verification
echo ""
echo "[STEP 3/5] Verifying Merkle Catch DAG Tree Integrity..."
"$PYTHON_BIN" "${SCRIPT_DIR}/merkle_catch_dag.py" --verify
MERKLE_ROOT="$(cat "${ROOT}/memory/catch_log/merkle_root.hash" 2>/dev/null || echo "N/A")"
echo "🟢 [MERKLE DAG ROOT HASH] ${MERKLE_ROOT}"

# Step 4: 3-Agent Live Local Ollama Quorum Deliberation (MOVE 1 & MOVE 2)
echo ""
echo "[STEP 4/5] Executing 3-Agent Live Local Ollama Quorum (Zero Cloud Tokens)..."
"$PYTHON_BIN" "${SCRIPT_DIR}/local_quorum_deliberation.py" "Turn-key enterprise boot verification."

# Step 5: Voice Dead Man's Switch Heartbeat Check
echo ""
echo "[STEP 5/5] Checking Voice Dead Man's Switch Heartbeat..."
bash "${SCRIPT_DIR}/voice_deadman_switch.sh" 15

echo ""
echo "================================================================="
echo "🟢 XORAS TURN-KEY ENTERPRISE SYSTEM: 100% VERIFIED & READY TO SHIP"
echo "================================================================="
echo "• Stage Target  : http://127.0.0.1:8080/customer_app.html"
echo "• Merkle Root   : ${MERKLE_ROOT}"
echo "• Speech Quorum : Maxx (Lead), Vance (Critic), Dr. Eden (Human Lens)"
echo "• Pipeline Law  : Pure Bash Speech Gate + Dead Man's Switch Active"
echo "================================================================="
