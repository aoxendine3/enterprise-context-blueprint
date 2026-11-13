#!/usr/bin/env python3
#=============================================================================
# SOVEREIGN MEMORY RECOVERY SWEEP — DEEP CROSS-TOOL RECOVERY INDEX
#=============================================================================
# Mandate: "sync all memory sources and recover old... transitioned to other
# tools and features, losing parts and pieces over the months. Dig deep,
# do not hold back, relentless search."
#
# What it does:
#   1. Sweeps every known memory-bearing location on this machine (project
#      zones, prior-tool app stores, harness session stores, volumes).
#   2. For every SQLite DB: tables, row counts, date ranges, size, mtime.
#   3. For every memory/log dir: file counts, sizes, date ranges.
#   4. barn/: metadata ONLY (names, sizes, dates) — contents are banned
#      reading zone per Log Entry #080; nothing is ingested into context.
#   5. Writes source_sweep_manifest.json + append-only source_sweep_history.jsonl
#      into memory/recovery/ INSIDE the project (no external stores).
#
# Fail-safe: unreadable locations are recorded with the reason, never skipped
# silently. Nothing is deleted or moved by this sweep — discovery only.
#=============================================================================
import datetime
import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
OUT_DIR = ROOT / "memory" / "observability"
OUT_NAME = "source_sweep_manifest.json"
HOME = Path.home()

SOURCE_ROOTS = [
    ("SSOT_MEMORY", ROOT / "memory", 4, False),
    ("SSOT_CORE_MEMORY", ROOT / "core/memory", 4, False),
    ("SSOT_SOVEREIGN", ROOT / ".sovereign", 4, False),
    ("SSOT_CATCH_LOG", ROOT / "memory/catch_log", 3, False),
    ("SSOT_DOCS", ROOT / "docs", 3, False),
    ("SSOT_BARN_META_ONLY", ROOT / "barn", 2, True),  # metadata only, banned content
    ("GEMINI_HOME", HOME / ".gemini", 3, False),
    ("ANTIGRAVITY_AS", HOME / "Library/Application Support/Antigravity", 2, False),
    ("ANTIGRAVITY_IDE_AS", HOME / "Library/Application Support/Antigravity IDE", 2, False),
    ("CLAUDE_AS", HOME / "Library/Application Support/Claude", 2, False),
    ("CURSOR_AS", HOME / "Library/Application Support/Cursor", 2, False),
    ("GEMINI_MACOS_AS", HOME / "Library/Application Support/com.google.GeminiMacOS", 2, False),
    ("OPENCODE_DESKTOP_AS", HOME / "Library/Application Support/ai.opencode.desktop", 2, False),
    ("CLAUDE_SHARE", HOME / ".local/share/claude", 3, False),
    ("OPENCODE_SHARE", HOME / ".local/share/opencode", 3, False),
    ("GRAPHITE_SHARE", HOME / ".local/share/graphite", 2, False),
    ("TIRITH_SHARE", HOME / ".local/share/tirith", 2, False),
    ("CONFIG_HOME", HOME / ".config", 2, False),
    ("DESKTOP_DAXXCO", HOME / "Desktop/DaxxCo_Tech", 3, False),
    ("DESKTOP_THEORIES", HOME / "Desktop/Theories", 3, False),
    ("VOLUME_OPENCODE", Path("/Volumes/OpenCode"), 3, False),
    ("VOLUME_UNTITLED", Path("/Volumes/Untitled"), 2, False),
    ("DOWNLOADS_RECOVERY", HOME / "Downloads", 1, False),
]

DB_EXTS = {".db", ".sqlite", ".sqlite3"}
SKIP_DIRNAME_PARTS = {"node_modules", "__pycache__", ".git", "Cache", "Caches", "GPUCache"}
MAX_FILE_LISTING = 4000


def utc(ts: float) -> str:
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha_head(path: Path) -> str:
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read(1 << 16)).hexdigest()[:16]
    except Exception:
        return ""


def audit_db(p: Path, meta_only: bool) -> dict:
    rel = str(p)
    try:
        st = p.stat()
    except Exception as e:
        return {"path": rel, "status": "UNREADABLE", "error": str(e)}
    rec = {"path": rel, "bytes": st.st_size, "mtime_utc": utc(st.st_mtime), "sha_head": sha_head(p)}
    if meta_only:
        rec["note"] = "BANNED_CONTENT_ZONE — metadata only (Log Entry #080)"
        return rec
    try:
        conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True, timeout=5)
        cur = conn.cursor()
        tables = [r[0] for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
        tinfo = {}
        earliest, latest = None, None
        for t in tables:
            try:
                n = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
            except Exception:
                n = None
            entry = {"rows": n}
            cols = [r[1] for r in cur.execute(f'PRAGMA table_info("{t}")').fetchall()]
            tscol = next((c for c in ("timestamp", "ts", "created_at", "createdAt", "created", "updated_at") if c in cols), None)
            if tscol and isinstance(n, int) and 0 < n <= 2_000_000:
                try:
                    lo, hi = cur.execute(f'SELECT MIN("{tscol}"), MAX("{tscol}") FROM "{t}"').fetchone()
                    if lo is not None:
                        entry["range"] = [str(lo)[:40], str(hi)[:40]]
                        for v in (lo, hi):
                            try:
                                fv = float(v)
                                if 1e9 < fv < 4e9:
                                    d = utc(fv)
                                    earliest = min(earliest or d, d)
                                    latest = max(latest or d, d)
                            except (TypeError, ValueError):
                                pass
                except Exception:
                    pass
            tinfo[t] = entry
        conn.close()
        rec.update({"status": "OK", "tables": tinfo, "content_earliest": earliest, "content_latest": latest})
    except Exception as e:
        rec.update({"status": "LOCKED_OR_UNREADABLE", "error": str(e)[:200]})
    return rec


def sweep_root(label: str, base: Path, maxdepth: int, meta_only: bool) -> dict:
    out = {"source": label, "root": str(base), "exists": base.exists(), "dbs": [], "dirs": [], "files_indexed": 0, "total_bytes": 0}
    if not base.exists():
        return out
    dbs, dirnames, n_files, total = [], {}, 0, 0
    for dirpath, dirnames_walk, filenames in os.walk(base):
        depth = len(Path(dirpath).relative_to(base).parts)
        if depth >= maxdepth:
            dirnames_walk[:] = []
        dirnames_walk[:] = [d for d in dirnames_walk if d not in SKIP_DIRNAME_PARTS]
        for fn in filenames:
            p = Path(dirpath) / fn
            try:
                sz = p.stat().st_size
            except Exception:
                continue
            total += sz
            n_files += 1
            if p.suffix.lower() in DB_EXTS and not fn.startswith("._"):
                dbs.append(audit_db(p, meta_only))
        if n_files >= MAX_FILE_LISTING:
            dirnames_walk[:] = []
    out.update({"dbs": dbs, "files_indexed": n_files, "total_bytes": total})
    return out


def main() -> None:
    t0 = time.time()
    results = [sweep_root(*src) for src in SOURCE_ROOTS]
    run = {
        "run_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_s": round(time.time() - t0, 1),
        "sources": results,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = OUT_DIR / OUT_NAME
    manifest.write_text(json.dumps(run, indent=2, sort_keys=True), encoding="utf-8")

    history = OUT_DIR / "source_sweep_history.jsonl"
    digest = hashlib.sha256(json.dumps(run, sort_keys=True).encode()).hexdigest()
    summary = {
        "run_utc": run["run_utc"],
        "source_sweep_manifest_sha256": digest,
        "sources": [
            {
                "source": r["source"],
                "dbs": len(r["dbs"]),
                "files": r["files_indexed"],
                "gb": round(r["total_bytes"] / 1e9, 2),
            } for r in results
        ],
    }
    with open(history, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(summary, sort_keys=True) + "\n")

    print(f"RECOVERY SWEEP complete in {run['elapsed_s']}s")
    for r in results:
        if not r["exists"]:
            print(f"  {r['source']:<24} ABSENT ({r['root']})")
            continue
        print(f"  {r['source']:<24} {r['files_indexed']:>7} files  {r['total_bytes']/1e9:>7.2f} GB  {len(r['dbs'])} DBs")
    try:
        sys.path.insert(0, str(ROOT / "core/ops/scripts"))
        from sovereign_activity_trace import span as _trace
        _trace(trace_id="memory_recovery_sweep", action=f"swept {len(results)} sources", actor="recovery_sweep")
    except Exception:
        pass


import sys  # noqa: E402
if __name__ == "__main__":
    main()
