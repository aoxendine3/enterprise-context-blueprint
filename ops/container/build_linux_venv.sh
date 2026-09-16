#!/usr/bin/env bash
# Xoras Systems Linux Venv Build & Execution Script
set -e

echo '[+] Creating Linux Virtual Environment...'
python3 -m venv /opt/xoras/venv
source /opt/xoras/venv/bin/activate

echo '[+] Installing Xoras High-Throughput Linux Dependencies...'
pip install --upgrade pip
pip install numpy soundfile requests flask urllib3

echo '[+] Launching Xoras Sovereign Stage on Port 8080...'
python ops/scripts/stage_server.py &
echo '[+] Linux Venv Build Complete & Operational!'
