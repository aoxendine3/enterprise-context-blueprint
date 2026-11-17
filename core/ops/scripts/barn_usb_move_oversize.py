#!/usr/bin/env python3
"""
barn_usb_move_oversize.py — move every misc/ file >=40MB to the external USB
barn, FAIL-CLOSED: copy -> sha256 both sides -> delete local only on match.
Kokoro voice model excluded (no proof it is unused). Manifest written
incrementally so a crash never loses the record of what moved.
"""

import hashlib
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone

MISC = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/misc"
DEST = "/Volumes/Untitled/SSOT_Agentic_Brain_External/misc_archive_20261117"
MANIFEST = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/catch_log/barn_misc_oversize_moves_20261117.json"
LOG = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/scratch/barn_usb_move.log"
KEEP = {"kokoro-v1_0.onnx"}
MIN_BYTES = 40 * 1024 * 1024


def log(m):
    line = f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] {m}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    t0 = time.time()
    os.makedirs(DEST, exist_ok=True)
    manifest = {"utc_started": datetime.now(timezone.utc).isoformat(),
                "destination": DEST, "law": "copy, verify sha256, then delete local; nothing deleted unverified",
                "moved": [], "failed": []}
    if os.path.exists(MANIFEST):
        with open(MANIFEST) as f:
            manifest = json.load(f)

    files = [os.path.join(MISC, n) for n in os.listdir(MISC)]
    files = [p for p in files if os.path.isfile(p) and not os.path.islink(p)
             and os.path.getsize(p) >= MIN_BYTES
             and os.path.basename(p) not in KEEP]
    files.sort(key=lambda p: -os.path.getsize(p))
    total = sum(os.path.getsize(p) for p in files)
    log(f"{len(files)} files, {total/1073741824:.1f} GB to move")

    for p in files:
        name = os.path.basename(p)
        if any(m["name"] == name for m in manifest["moved"]):
            log(f"SKIP {name} (already in manifest)")
            continue
        dst = os.path.join(DEST, name)
        sz = os.path.getsize(p)
        try:
            shutil.copyfile(p, dst)
            s_src = sha256(p)
            s_dst = sha256(dst)
            if s_src != s_dst:
                raise RuntimeError(f"sha256 mismatch src={s_src} dst={s_dst}")
            os.remove(p)
            manifest["moved"].append(
                {"name": name, "size": sz, "sha256": s_src,
                 "dest": dst, "utc": datetime.now(timezone.utc).isoformat()})
            log(f"MOVED {name} ({sz/1048576:.0f} MB) sha {s_src[:12]}")
        except Exception as e:
            manifest["failed"].append(
                {"name": name, "error": str(e),
                 "utc": datetime.now(timezone.utc).isoformat()})
            log(f"FAIL {name}: {e} (local copy KEPT)")
        with open(MANIFEST, "w") as f:
            json.dump(manifest, f, indent=1)

    log(f"=== done in {time.time()-t0:.0f}s: {len(manifest['moved'])} moved, "
        f"{len(manifest['failed'])} failed ===")
    return 0 if not manifest["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
