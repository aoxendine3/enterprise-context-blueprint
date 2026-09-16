#!/usr/bin/env bash
# ==============================================================================
# Hermes Copilot — macOS Production Launcher
# Sovereign Local Executive Gateway (Port 8085)
# ==============================================================================

set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${APP_DIR}:${PYTHONPATH:-}"

echo "=================================================================="
echo "  HERMES COPILOT — SOVEREIGN AGENT SUITE (macOS M-SERIES / INTEL)"
echo "=================================================================="

# Verify Python 3
if ! command -v python3 &>/dev/null; then
    echo "[-] Error: python3 not found on PATH." >&2
    exit 1
fi

# Verify Ollama Reachability
echo "[*] Checking Sovereign Local Inference Core (http://127.0.0.1:11434)..."
if curl -s http://127.0.0.1:11434/api/tags &>/dev/null; then
    echo "[+] Ollama inference engine detected and online."
else
    echo "[!] Notice: Ollama daemon not running. Embedded autonomous transformer will activate as fallback."
fi

# Pre-Execution Spoken Invariant via macOS CoreAudio / Kokoro
if [[ -f "${APP_DIR}/../../ops/scripts/agent_speak.sh" ]]; then
    bash "${APP_DIR}/../../ops/scripts/agent_speak.sh" maxx "Hermes Copilot macOS sovereign gateway launching on port 8085." || true
elif command -v say &>/dev/null; then
    say -v Samantha "Hermes Copilot macOS sovereign gateway launching on port 8085." &
fi

echo "[*] Booting Hermes Copilot Server on http://127.0.0.1:8085 ..."
python3 "${APP_DIR}/server.py" &
SERVER_PID=$!
echo "${SERVER_PID}" > "${APP_DIR}/.server.pid"

sleep 1.5

# Automatically open Web UI in default macOS browser (Safari / Chrome)
if command -v open &>/dev/null; then
    open "http://127.0.0.1:8085/"
fi

echo "[+] Hermes Copilot successfully launched (PID: ${SERVER_PID})."
echo "[+] Web App:     http://127.0.0.1:8085/"
echo "[+] Landing Page: http://127.0.0.1:8085/landing.html"
echo "[+] Press Ctrl+C to stop the server."

wait "${SERVER_PID}"
