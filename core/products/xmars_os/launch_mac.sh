#!/usr/bin/env bash
# ==============================================================================
# XMARS.os — macOS Production Launcher
# Sovereign Neural Command Operating System (Port 8085)
# ==============================================================================

set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${APP_DIR}:${PYTHONPATH:-}"

echo "=================================================================="
echo "  XMARS.os — SOVEREIGN NEURAL COMMAND OS (macOS M-SERIES / INTEL)"
echo "=================================================================="

# Check Python 3
if ! command -v python3 &>/dev/null; then
    echo "[-] Error: python3 not found on PATH." >&2
    exit 1
fi

# Pre-execution audio dispatch via macOS CoreAudio / Kokoro M4
if [[ -f "${APP_DIR}/../../ops/scripts/agent_speak.sh" ]]; then
    bash "${APP_DIR}/../../ops/scripts/agent_speak.sh" maxx "XMARS dot os sovereign neural command operating system launching on port 8085." || true
elif command -v say &>/dev/null; then
    say -v Samantha "XMARS dot os sovereign neural command operating system launching on port 8085." &
fi

echo "[*] Booting XMARS.os Server on http://127.0.0.1:8085 ..."
python3 "${APP_DIR}/server.py" &
SERVER_PID=$!
echo "${SERVER_PID}" > "${APP_DIR}/.server.pid"

sleep 1.5

# Automatically open Web UI in default browser
if command -v open &>/dev/null; then
    open "http://127.0.0.1:8085/"
fi

echo "[+] XMARS.os successfully active (PID: ${SERVER_PID})."
echo "[+] Command Canvas: http://127.0.0.1:8085/"
echo "[+] Executive View: http://127.0.0.1:8085/landing.html"
echo "[+] Press Ctrl+C to stop XMARS.os."

wait "${SERVER_PID}"
