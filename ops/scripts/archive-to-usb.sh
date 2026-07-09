#!/usr/bin/env bash
# archive-to-usb.sh — Cold archive per DEDUPE_MANIFEST.md
# Usage:
#   bash ops/scripts/archive-to-usb.sh              # copy only (safe default)
#   bash ops/scripts/archive-to-usb.sh --finalize   # remove local copies after verified rsync
set -euo pipefail

XORAS_ROOT="${XORAS_ROOT:-$HOME/Desktop/Xoras_Workspace}"
USB_VOL="${USB_VOL:-/Volumes/USB_Backup}"
STAMP="$(date +%Y-%m-%d)"
DEST="$USB_VOL/Xoras_Cold_Archive/$STAMP"
FINALIZE=0

if [[ "${1:-}" == "--finalize" ]]; then
  FINALIZE=1
fi

if [[ ! -d "$USB_VOL" ]]; then
  echo "ERROR: USB not mounted at $USB_VOL"
  echo "Plug in your USB drive (should mount as USB_Backup) and run again."
  echo "Or: USB_VOL=/Volumes/YourDriveName bash ops/scripts/archive-to-usb.sh"
  exit 2
fi

FREE_KB=$(df -k "$USB_VOL" | awk 'NR==2 {print $4}')
FREE_GB=$(awk "BEGIN {printf \"%.1f\", $FREE_KB/1024/1024}")
echo "=== XORAS USB ARCHIVE ==="
echo "USB:  $USB_VOL (${FREE_GB} GB free)"
echo "Dest: $DEST"
echo ""

if (( FREE_KB < 5242880 )); then
  echo "WARNING: Less than 5 GB free on USB. Proceeding anyway."
fi

mkdir -p "$DEST/backups_and_configs_archive" "$DEST/dist_artifacts" "$DEST/logs"

copy_tree() {
  local label="$1"
  local src="$2"
  local dst="$3"
  if [[ ! -e "$src" ]]; then
    echo "SKIP: $label — not found ($src)"
    return 0
  fi
  local size
  size=$(du -sh "$src" 2>/dev/null | awk '{print $1}')
  echo "COPY: $label ($size) → $dst"
  rsync -a --info=stats2 "$src/" "$dst/" 2>&1 | tail -3
  echo "  done."
}

copy_tree "Backups_and_Configs/_Archive" \
  "$XORAS_ROOT/Backups_and_Configs/_Archive" \
  "$DEST/backups_and_configs_archive"

if [[ -d "$XORAS_ROOT/dist/sovereign_stack" ]] && [[ -n "$(ls -A "$XORAS_ROOT/dist/sovereign_stack" 2>/dev/null)" ]]; then
  copy_tree "dist/sovereign_stack" \
    "$XORAS_ROOT/dist/sovereign_stack" \
    "$DEST/dist_artifacts/sovereign_stack"
fi

DESKTOP_DMG="$HOME/Desktop/Xoras_Sovereign_AI_Stack.dmg"
CANON_DMG="$XORAS_ROOT/dist/Xoras_Sovereign_AI_Stack.dmg"
if [[ -f "$DESKTOP_DMG" ]]; then
  if [[ -f "$CANON_DMG" ]] && cmp -s "$DESKTOP_DMG" "$CANON_DMG"; then
    echo "COPY: Desktop duplicate DMG (hash match) → $DEST/dist_artifacts/"
    cp -p "$DESKTOP_DMG" "$DEST/dist_artifacts/Desktop_Xoras_Sovereign_AI_Stack.dmg"
  else
    echo "COPY: Desktop DMG (no canonical match — keeping both) → $DEST/dist_artifacts/"
    cp -p "$DESKTOP_DMG" "$DEST/dist_artifacts/Desktop_Xoras_Sovereign_AI_Stack.dmg"
  fi
fi

# Manifest
python3 - <<PY
import json, os, subprocess, datetime
root = os.path.expanduser("$XORAS_ROOT")
dest = "$DEST"
manifest = {
    "created": datetime.datetime.now().isoformat(),
    "xoras_root": root,
    "usb_dest": dest,
    "groups": [],
}
for label, sub in [
    ("backups_and_configs_archive", "backups_and_configs_archive"),
    ("dist_artifacts", "dist_artifacts"),
]:
    p = os.path.join(dest, sub)
    if os.path.isdir(p):
        out = subprocess.check_output(["du", "-sk", p], text=True).split()[0]
        manifest["groups"].append({"name": label, "path": p, "size_kb": int(out)})
out_path = os.path.join(dest, "dedupe_manifest.json")
with open(out_path, "w") as f:
    json.dump(manifest, f, indent=2)
print(f"Wrote {out_path}")
PY

echo ""
echo "Archive copy complete."

if [[ "$FINALIZE" -eq 1 ]]; then
  echo "FINALIZE: removing local cold archive (already on USB)..."
  if [[ -d "$XORAS_ROOT/Backups_and_Configs/_Archive" ]]; then
    rm -rf "$XORAS_ROOT/Backups_and_Configs/_Archive"
    mkdir -p "$XORAS_ROOT/Backups_and_Configs/_Archive"
    echo "Offloaded _Archive — placeholder dir recreated."
  fi
  if [[ -f "$DESKTOP_DMG" ]] && [[ -f "$CANON_DMG" ]] && cmp -s "$DESKTOP_DMG" "$CANON_DMG"; then
    rm -f "$DESKTOP_DMG"
    echo "Removed duplicate Desktop DMG."
  fi
  echo "Reclaimed local disk. USB is now the cold store for this pass."
else
  echo "Local copies kept. Re-run with --finalize after you verify files on USB."
fi

echo "RESULT: GREEN — USB archive finished."
