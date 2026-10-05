#!/usr/bin/env bash
# ==============================================================================
# XMARS.os — Standalone GitHub Repository Initializer (macOS / Linux)
# ==============================================================================

set -euo pipefail

REPO_NAME="${1:-XMARS.os}"
VISIBILITY="${2:-private}"

echo "=================================================================="
echo "  XMARS.os STANDALONE GITHUB REPOSITORY INITIALIZER"
echo "=================================================================="

cd "$(dirname "${BASH_SOURCE[0]}")"

if [ ! -d ".git" ]; then
    echo "[*] Initializing local git repository..."
    git init
    git branch -M main
fi

echo "[*] Staging all XMARS.os assets..."
git add .
git commit -m "feat(xmars): Initial commit of XMARS.os Sovereign Neural Command Operating System" || true

if command -v gh &>/dev/null; then
    echo "[*] GitHub CLI detected. Creating remote repository '${REPO_NAME}'..."
    gh repo create "${REPO_NAME}" --"${VISIBILITY}" --source=. --remote=origin --push
    echo "[+] Repository created and synchronized successfully!"
else
    echo "[!] GitHub CLI (gh) not detected."
    echo "[*] To link to a remote repository manually:"
    echo "    1. Create repository '${REPO_NAME}' at https://github.com/new"
    echo "    2. Run: git remote add origin https://github.com/YOUR_USER/${REPO_NAME}.git"
    echo "    3. Run: git push -u origin main"
fi
