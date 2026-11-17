#!/usr/bin/env python3
"""
barn_usb_move_oversize_v2.py — move every misc/ file >=40MB to the external
USB barn (ExFAT, slow ~4MB/s), SPARSE-AWARE, FAIL-CLOSED.

For each file:
  allocated = real blocks used (du); apparent = st_size.
  If allocated < apparent/2  -> sparse giant: stream `gzip -c` to USB as
      <name>.gz (zeros collapse; output ~ allocated size), verify with
      `gzip -t` (gzip CRC32 covers content integrity), record sha256 of
      the .gz, then delete local ONLY after `gzip -t` passes.
  Else -> plain copy, sha256 both sides, delete local only on match.

Excluded: kokoro-v1_0.onnx (voice model, no proof it is unused).
Manifest written incrementally. On any failure the LOCAL copy is kept.
"""

import hashlib
import json
import os
import subprocess
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


def allocated(p):
    r = subprocess.run(["du", "-k", p], capture_output=True, text=True)
    return int(r.stdout.split()[0]) * 1024 if r.returncode == 0 else os.path.getsize(p)


def move_sparse(name, src, dst_gz, entry_base):
    t = time.time()
    with open(src, "rb") as f, open(dst_gz, "wb") as out:
        gz = subprocess.Popen(["gzip", "-c"], stdin=f, stdout=out)
        gz.wait()
        if gz.returncode != 0:
            raise RuntimeError(f"gzip exit {gz.returncode}")
    r = subprocess.run(["gzip", "-t", dst_gz], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"gzip -t verification failed: {r.stderr[:200]}")
    s = sha256(dst_gz)
    os.remove(src)
    e = dict(entry_base)
    e.update({"mode": "sparse-gzip", "stored_sha256": s,
              "verify": "gzip -t CRC32 pass", "local_deleted": True,
              "utc": datetime.now(timezone.utc).isoformat()})
    log(f"MOVED(sparse) {name}: apparent {entry_base['apparent']/1048576:.0f}MB -> "
        f"{os.path.getsize(dst_gz)/1048576:.0f}MB gz, verified, local removed, "
        f"{time.time()-t:.0f}s")
    return e


def move_plain(name, src, dst, entry_base):
    t = time.time()
    import shutil
    shutil.copyfile(src, dst)
    s1, s2 = sha256(src), sha256(dst)
    if s1 != s2:
        raise RuntimeError(f"sha256 mismatch {s1[:12]} != {s2[:12]}")
    os.remove(src)
    e = dict(entry_base)
    e.update({"mode": "copy", "sha256": s1, "local_deleted": True,
              "utc": datetime.now(timezone.utc).isoformat()})
    log(f"MOVED {name}: {entry_base['size']/1048576:.0f}MB, sha {s1[:12]}, "
        f"{time.time()-t:.0f}s")
    return e


def main():
    t0 = time.time()
    os.makedirs(DEST, exist_ok=True)
    if os.path.exists(MANIFEST):
        manifest = json.load(open(MANIFEST))
    else:
        manifest = {"utc_started": datetime.now(timezone.utc).isoformat(),
                    "destination": DEST,
                    "law": "copy/compress-stream, verify, then delete local; nothing deleted unverified",
                    "moved": [], "failed": []}

    files = [os.path.join(MISC, n) for n in os.listdir(MISC)]
    files = [p for p in files if os.path.isfile(p) and not os.path.islink(p)
             and os.path.getsize(p) >= MIN_BYTES
             and os.path.basename(p) not in KEEP]
    files.sort(key=lambda p: -allocated(p))
    tot_alloc = sum(allocated(p) for p in files)
    log(f"{len(files)} files, {tot_alloc/1073741824:.1f} GB allocated to move")

    for p in files:
        name = os.path.basename(p)
        if any(m["name"] == name for m in manifest["moved"]):
            log(f"SKIP {name} (already moved)")
            continue
        sz = os.path.getsize(p)
        alloc = allocated(p)
        base = {"name": name, "size": sz, "apparent": sz, "allocated": alloc}
        try:
            if alloc * 2 < sz:
                e = move_sparse(name, p, os.path.join(DEST, name + ".gz"), base)
            else:
                e = move_plain(name, p, os.path.join(DEST, name), base)
            manifest["moved"].append(e)
        except Exception as ex:
            manifest["failed"].append({"name": name, "error": str(ex),
                                       "utc": datetime.now(timezone.utc).isoformat()})
            log(f"FAIL {name}: {ex} (local copy KEPT)")
            for cand in (os.path.join(DEST, name), os.path.join(DEST, name + ".gz")):
                try:
                    if os.path.exists(cand):
                        os.remove(cand)  # remove partial
                except OSError:
                    pass
        with open(MANIFEST, "w") as f:
            json.dump(manifest, f, indent=1)

    log(f"=== done in {time.time()-t0:.0f}s: {len(manifest['moved'])} moved, "
        f"{len(manifest['failed'])} failed ===")
    return 0 if not manifest["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
