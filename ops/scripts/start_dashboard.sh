#!/usr/bin/env bash
# =============================================================================
# XORAS SYSTEM: DUAL-OS (MACOS/LINUX) SOVEREIGN DASHBOARD LAUNCHER
# Standardized Bash supervisor for dev/prod web dashboard serving.
# =============================================================================
set -euo pipefail

PORT="${1:-8080}"
DASHBOARD="${2:-customer_app.html}"
UI_DIR="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui"

echo "================================================================="
echo "XORAS DASHBOARD SUPERVISOR (PORT $PORT)"
echo "================================================================="

# 1. Check if server is already running on PORT
if lsof -i :"$PORT" >/dev/null 2>&1; then
    echo "[✓] Web server already active on port $PORT."
else
    echo "[!] Starting background HTTP server on port $PORT..."
    cd "$UI_DIR"
    nohup python3 -m http.server "$PORT" > /tmp/xoras_dashboard_server.log 2>&1 &
    sleep 1
    if lsof -i :"$PORT" >/dev/null 2>&1; then
        echo "[✓] Web server launched successfully on port $PORT."
    else
        echo "[❌] Failed to launch web server on port $PORT. Check /tmp/xoras_dashboard_server.log"
        exit 1
    fi
fi

# 2. Cross-platform URL opener (macOS open vs Linux xdg-open)
URL="http://127.0.0.1:${PORT}/${DASHBOARD}"
if [[ ! -f "${UI_DIR}/${DASHBOARD}" ]]; then
    echo "[❌] Dashboard file not found: ${UI_DIR}/${DASHBOARD}"
    exit 1
fi
echo "[🚀] Opening dashboard at: $URL"

if command -v open >/dev/null 2>&1; then
    open "$URL"
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$URL"
else
    echo "[i] Please open $URL in your browser."
fi

echo "[✓] Dashboard ready."
