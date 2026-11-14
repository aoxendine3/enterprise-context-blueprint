#!/usr/bin/env python3
"""
=============================================================================
ESTATE DEEP DIGEST — EVERY FOLDER, EVERY FILE
=============================================================================
Walks a tree and reports, per top-level entry: file count, bytes, zero-byte
files, extension histogram, the five largest files, and the newest/oldest
timestamps. Used to find what is actually in the estate instead of guessing.

Usage: estate_deep_digest.py <root> [out.json] [skip_dir_names]
=============================================================================
"""

import json
import os
import sys
import time
from collections import Counter

SKIP = {".git", "node_modules", ".venv", "__pycache__", ".next", "target", ".pytest_cache"}


def digest_entry(path: str, name: str) -> dict:
    stats = {
        "files": 0,
        "bytes": 0,
        "zero": 0,
        "ext": Counter(),
        "largest": [],
        "newest": 0.0,
        "oldest": 9e18,
        "path": path,
    }
    if os.path.isfile(path) and not os.path.islink(path):
        try:
            st = os.stat(path)
        except OSError:
            return {"error": "unreadable", "path": path}
        stats.update(files=1, bytes=st.st_size, zero=1 if st.st_size == 0 else 0,
                     ext={os.path.splitext(name)[1].lower() or "(none)": 1},
                     largest=[(st.st_size, path)],
                     newest=st.st_mtime, oldest=st.st_mtime)
    else:
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in SKIP]
            for fn in files:
                fp = os.path.join(root, fn)
                try:
                    st = os.stat(fp)
                except OSError:
                    continue
                stats["files"] += 1
                stats["bytes"] += st.st_size
                stats["ext"][os.path.splitext(fn)[1].lower() or "(none)"] += 1
                if st.st_size == 0:
                    stats["zero"] += 1
                stats["newest"] = max(stats["newest"], st.st_mtime)
                stats["oldest"] = min(stats["oldest"], st.st_mtime)
                stats["largest"].append((st.st_size, fp))
        stats["largest"] = sorted(stats["largest"], reverse=True)[:5]
    stats["ext"] = dict(stats["ext"].most_common(8))
    for k in ("newest", "oldest"):
        v = stats.get(k)
        stats[k] = time.strftime("%Y-%m-%d", time.gmtime(v)) if v not in (0.0, 9e18) else None
    stats["largest"] = [{"mb": round(s / 1e6, 2), "path": p} for s, p in stats["largest"]]
    return stats


def walk(root: str) -> dict:
    out = {}
    try:
        entries = sorted(os.scandir(root), key=lambda e: e.name)
    except Exception as exc:
        return {"error": str(exc)}
    for e in entries:
        if e.name in SKIP:
            continue
        try:
            out[e.name] = digest_entry(e.path, e.name)
        except Exception:
            out[e.name] = {"error": "unreadable", "path": e.path}
    return out


def main() -> int:
    root = os.path.abspath(sys.argv[1])
    out_path = sys.argv[2] if len(sys.argv) > 2 else "/tmp/estate_digest.json"
    payload = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "root": root,
        "entries": walk(root),
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1)
    total_files = sum(v.get("files", 0) for v in payload["entries"].values() if isinstance(v, dict))
    total_bytes = sum(v.get("bytes", 0) for v in payload["entries"].values() if isinstance(v, dict))
    print(f"DIGEST WRITTEN {out_path}: {len(payload['entries'])} entries, {total_files} files, {total_bytes/1e9:.2f} GB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
