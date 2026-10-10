#!/usr/bin/env bash
# XORAS Systems LLC — Clean & Build Release Helper

set -e

echo "[XORAS BUILD] Cleaning prior build artifacts..."
rm -rf build/ dist/ *.egg-info xoras_agent_framework.egg-info

echo "[XORAS BUILD] Re-building source distribution and wheel package..."
python3 setup.py sdist bdist_wheel

echo "[XORAS BUILD] Verifying package artifacts with twine..."
python3 -m twine check dist/*

echo "[XORAS BUILD] Build completed and verified successfully."
