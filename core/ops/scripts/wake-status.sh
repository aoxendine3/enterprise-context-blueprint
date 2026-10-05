#!/usr/bin/env bash
# wake-status.sh — Plain-English wake check for Anthony
# Usage: bash ops/scripts/wake-status.sh
set -euo pipefail

XORAS_ROOT="${XORAS_ROOT:-$HOME/Desktop/Xoras_Workspace}"
SOURCE="$XORAS_ROOT/AI_Core/Xoras_Project/xoras-core/Source"
STATUS_FILE="$SOURCE/.xoras_wake_status.json"

echo "=== XORAS WAKE STATUS ==="
echo "Time: $(date '+%Y-%m-%d %H:%M')"
echo ""

if [[ ! -d "$SOURCE" ]]; then
  echo "STATUS: ERROR — Source directory not found"
  echo "Expected: $SOURCE"
  exit 1
fi

if [[ ! -f "$STATUS_FILE" ]]; then
  echo "STATUS: OFFLINE — No wake status file yet"
  echo "Run: cd $SOURCE && python3 xoras_wake.py"
  exit 2
fi

# Parse status without jq dependency
phase=$(python3 -c "import json; d=json.load(open('$STATUS_FILE')); print(d.get('phase','?'))" 2>/dev/null || echo "?")
status=$(python3 -c "import json; d=json.load(open('$STATUS_FILE')); print(d.get('status','?'))" 2>/dev/null || echo "?")
message=$(python3 -c "import json; d=json.load(open('$STATUS_FILE')); print(d.get('message',''))" 2>/dev/null || echo "")
lock_mode=$(python3 -c "import json; d=json.load(open('$STATUS_FILE')); print(d.get('persona_lock_mode','?'))" 2>/dev/null || echo "?")

echo "Phase:  $phase"
echo "Status: $status"
echo "Lock:   $lock_mode"
echo "Note:   $message"
echo ""

case "$phase" in
  READY)   echo "RESULT: GREEN — Wake is ready."; exit 0 ;;
  FAILED)  echo "RESULT: RED — Wake failed. Tell your agent to fix."; exit 1 ;;
  *)       echo "RESULT: AMBER — Wake may be running or stale."; exit 2 ;;
esac
