#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Sync Master Audit Reports directly to Mac Desktop (/Users/ajoxendine68/Desktop)
# -----------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

SOURCE_DOC="${REPO_ROOT}/XORAS_MASTER_AUDIT_GROUND_UP_REWORK_AND_BYZANTINE_TEST.md"
TARGET_DESKTOPS=(
  "/Users/ajoxendine68/Desktop"
  "${HOME}/Desktop"
)

if [ ! -f "$SOURCE_DOC" ]; then
  echo "[-] Master audit document not found at: $SOURCE_DOC" >&2
  exit 1
fi

for dest_dir in "${TARGET_DESKTOPS[@]}"; do
  if [ -d "$dest_dir" ]; then
    target_path="${dest_dir}/XORAS_MASTER_AUDIT_GROUND_UP_REWORK_AND_BYZANTINE_TEST.md"
    cp -f "$SOURCE_DOC" "$target_path"
    echo "[✓] Synced Master Audit to Mac Desktop: $target_path"
  fi
done

echo "[✓] Master Audit Report is live on Mac Desktop."
