#!/usr/bin/env bash
# Verification-only cockpit gate. Never regenerates dist assets.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COCKPIT="$REPO/workspaces/telemetry_cockpit"
DIST="$COCKPIT/dist"

echo "[cockpit] structural bundle verification"
python3 "$COCKPIT/tools/verify_bundle.py" "$DIST/evidence-bundle.json"

echo "[cockpit] shipped asset lock"
python3 "$COCKPIT/tools/verify_assets.py" "$DIST"

echo "[cockpit] Python RAW gate tests"
python3 -m unittest discover -s "$COCKPIT/tests" -p 'test_*.py' -v

echo "[cockpit] full suite with enforced coverage floor (80% line)"
# Capture node's output AND exit code explicitly: with `set -e` a non-zero node
# exit used to abort this script before any message, swallowing the real error
# (fail-closed either way — this only makes the failure visible).
set +e
COVERAGE_OUTPUT="$(node --experimental-test-coverage --test "$COCKPIT/tests/"*.test.mjs 2>&1)"
NODE_RC=$?
set -e
printf '%s\n' "$COVERAGE_OUTPUT"
if [ "$NODE_RC" -ne 0 ]; then
  echo "COVERAGE GATE FAILED: node test suite exited rc=$NODE_RC (output above)" >&2
  exit 1
fi
LINE_COVERAGE="$(printf '%s\n' "$COVERAGE_OUTPUT" | awk -F'|' '/all files/ {gsub(/[ ]/,"",$2); print $2; exit}')"
if [ -z "$LINE_COVERAGE" ]; then
  echo "COVERAGE GATE FAILED: no coverage summary found" >&2
  exit 1
fi
python3 - "$LINE_COVERAGE" <<'PY'
import sys
value = float(sys.argv[1])
if value < 80.0:
    print(f"COVERAGE GATE FAILED: {value:.2f}% < 80%", file=sys.stderr)
    raise SystemExit(1)
print(f"COVERAGE GATE PASSED: {value:.2f}% >= 80%")
PY

echo "[cockpit] VERIFIED STRUCTURAL GATE"
