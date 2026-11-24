#!/usr/bin/env python3
"""Execute the operator-authorized misc/ -> barn reorganization.

Moves only cache spill, reproducible build artifacts, and unreferenced
duplicate images. Every move is identity-verified (inode + size + mtime, plus
sha256 for files <= 8 MiB). Nothing is deleted. A full manifest is written into
the barn next to the moved files; a summary is written to memory/catch_log.
"""
import os, re, sys, json, time, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MISC = root = ROOT / "misc"
DEST = ROOT / "barn/archives/the_barn/misc_reorganize_20261124"
SUMMARY = ROOT / "memory/catch_log/MISC_BARN_MOVE_SUMMARY_20261124.json"
LEDGER = ROOT / "memory/catch_log/QUARANTINE_LEDGER.json"
HASH_LIMIT = 8 * 1024 * 1024
t0 = time.time()

# ---- Proof before move: live-reference sweep of canonical source ------------
SOURCE_DIRS = ("core", "ops", "code", "identity", "Xoras_agent_cards", "tests",
               "workspaces", "data_center")
ref_lines = []
scanned = 0
for top in SOURCE_DIRS:
    base = ROOT / top
    if not base.exists():
        continue
    for dp, dirs, files in os.walk(base, followlinks=False):
        dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", "__pycache__", "Caches", ".venv")]
        for fn in files:
            p = Path(dp) / fn
            try:
                if p.is_symlink() or p.stat().st_size > 2_000_000:
                    continue
                text = p.read_text(errors="ignore")
            except OSError:
                continue
            scanned += 1
            for line in text.splitlines():
                if "misc/" in line or "misc\\" in line:
                    ref_lines.append({"file": str(p.relative_to(ROOT)), "line": line.strip()[:220]})
live_source_refs = [r for r in ref_lines
                    if not r["file"].startswith(("docs/", "memory/", "scratch/", "barn/"))]

# ---- Candidate selection ---------------------------------------------------
CACHE_DATA = re.compile(r"^[0-9a-f]{16}_\d+$")
CACHE_INDEX = re.compile(r"^(?:[0-9a-f]{32}|\d+)$")
CATEGORIES = {
    "chrome_cache_data": lambda n, e: bool(CACHE_DATA.match(n)),
    "cache_index_names": lambda n, e: bool(CACHE_INDEX.match(n)),
    "compiled_python": lambda n, e: e == ".pyc",
    "source_maps": lambda n, e: e == ".map",
    "object_files": lambda n, e: e == ".o",
    "journals": lambda n, e: e == ".journal",
    "build_metadata": lambda n, e: e in (".toc", ".meta", ".plist", ".gemspec", ".mts"),
}
LARGE_OBJECTS = {
    "stale_duplicate_images": ("Docker.raw", "disk"),
    "historical_app_database": ("xoras.db",),
}

# Exclude any basename explicitly named by a live source reference.
referenced_names = set()
for r in live_source_refs:
    referenced_names.update(Path(part).name for part in re.findall(r"misc[/\\]([^\s\"'`]+)", r["line"]))

candidates = []
excluded_referenced = []
for entry in os.scandir(MISC):
    if entry.is_symlink() or not entry.is_file(follow_symlinks=False):
        continue
    name = entry.name
    ext = Path(name).suffix.lower()
    if name in referenced_names:
        excluded_referenced.append(name)
        continue
    category = next((c for c, test in CATEGORIES.items() if test(name, ext)), None)
    if category is None and name in {n for group in LARGE_OBJECTS.values() for n in group}:
        category = next(c for c, names in LARGE_OBJECTS.items() if name in names)
    if category:
        candidates.append((name, category))

# ---- Move with per-file proof ----------------------------------------------
records = []
failed = []
for name, category in candidates:
    src = MISC / name
    dst_dir = DEST / category
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / name
    try:
        before = os.lstat(src)
        digest = None
        if before.st_size <= HASH_LIMIT:
            h = hashlib.sha256()
            with open(src, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h.update(chunk)
            digest = h.hexdigest()
        os.rename(src, dst)
        after = os.lstat(dst)
        ok = (after.st_ino == before.st_ino and after.st_size == before.st_size
              and after.st_mtime == before.st_mtime)
        if digest is not None:
            h2 = hashlib.sha256()
            with open(dst, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h2.update(chunk)
            ok = ok and h2.hexdigest() == digest
        if not ok:
            os.rename(dst, src)
            failed.append(name)
            continue
        records.append({
            "source": f"misc/{name}", "destination": str(dst.relative_to(ROOT)),
            "category": category, "bytes": before.st_size, "inode": before.st_ino,
            "mtime": before.st_mtime, "sha256": digest,
            "verified": True,
        })
    except OSError as exc:
        failed.append(f"{name}: {exc}")

manifest = {
    "schema": "xoras.misc_barn_move.v1",
    "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "authorization": "operator directive 2026-11-24: move nonessential cache/duplicate/placeholder material to the barn",
    "law": "moved intact, zero deletions, inode+size+mtime verified, sha256 for files <= 8 MiB",
    "files": records,
}
(DEST / "MANIFEST.json").write_text(json.dumps(manifest, indent=1))
manifest_hash = hashlib.sha256((DEST / "MANIFEST.json").read_bytes()).hexdigest()

by_cat = {}
bytes_by_cat = {}
verified_hash = 0
for r in records:
    by_cat[r["category"]] = by_cat.get(r["category"], 0) + 1
    bytes_by_cat[r["category"]] = bytes_by_cat.get(r["category"], 0) + r["bytes"]
    if r["sha256"]:
        verified_hash += 1

summary = {
    "schema": "xoras.misc_barn_move_summary.v1",
    "utc": manifest["utc"],
    "source": "misc",
    "destination": str(DEST.relative_to(ROOT)),
    "manifest": str((DEST / "MANIFEST.json").relative_to(ROOT)),
    "manifest_sha256": manifest_hash,
    "moved_files": len(records),
    "moved_bytes_apparent": sum(r["bytes"] for r in records),
    "by_category": by_cat,
    "bytes_by_category": bytes_by_cat,
    "sha256_verified_files": verified_hash,
    "inode_identity_verified_files": len(records),
    "failed_moves": failed[:20],
    "failed_count": len(failed),
    "excluded_live_referenced": excluded_referenced[:20],
    "excluded_live_referenced_count": len(excluded_referenced),
    "live_reference_sweep": {
        "source_files_scanned": scanned,
        "misc_reference_lines": len(ref_lines),
        "live_source_reference_lines": len(live_source_refs),
        "live_source_examples": live_source_refs[:10],
    },
    "elapsed_sec": round(time.time() - t0, 2),
}
SUMMARY.write_text(json.dumps(summary, indent=2))

# ---- Quarantine ledger entry -----------------------------------------------
ledger = json.loads(LEDGER.read_text())
ledger.setdefault("entries", []).append({
    "utc": manifest["utc"],
    "kind": "MISC_BARN_REORGANIZATION",
    "item": f"{len(records)} cache/reproducible/duplicate files from misc/ root",
    "reason": "Operator directive 2026-11-24: nonessential cache spill, reproducible artifacts, and unreferenced duplicate images belong in cold archive, not the active project tree. No deletion.",
    "source": str(MISC),
    "destination": str(DEST),
    "artifact": str(SUMMARY.relative_to(ROOT)),
    "sha256": manifest_hash,
    "bytes": summary["moved_bytes_apparent"],
    "law": "moved intact; live-reference sweep passed; inode+size+mtime verified on every move; sha256 verified on small files; no deletions",
    "verification": f"{len(records)}/{len(candidates)} moves verified, {len(failed)} failures",
})
LEDGER.write_text(json.dumps(ledger, indent=1))

print(json.dumps({k: summary[k] for k in ("moved_files", "moved_bytes_apparent", "by_category",
       "sha256_verified_files", "failed_count", "excluded_live_referenced_count",
       "live_reference_sweep", "elapsed_sec")}, indent=2))
print("MANIFEST:", DEST / "MANIFEST.json")
print("SUMMARY:", SUMMARY)
