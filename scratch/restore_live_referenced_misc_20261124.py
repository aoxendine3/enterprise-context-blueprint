#!/usr/bin/env python3
"""Restore any moved file that a live source reference still names.

Runs a fresh canonical-source sweep, expands wildcard references against the
move manifest, restores matching files to their original misc/ path with inode
proof, and rewrites the manifest + summary + ledger accordingly.
"""
import os, re, json, fnmatch, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MISC = ROOT / "misc"
DEST = ROOT / "barn/archives/the_barn/misc_reorganize_20261124"
MANIFEST = DEST / "MANIFEST.json"
SUMMARY = ROOT / "memory/catch_log/MISC_BARN_MOVE_SUMMARY_20261124.json"
LEDGER = ROOT / "memory/catch_log/QUARANTINE_LEDGER.json"

manifest = json.loads(MANIFEST.read_text())
summary = json.loads(SUMMARY.read_text())
records = manifest["files"]
by_name = {Path(r["source"]).name: r for r in records}

SOURCE_DIRS = ("core", "ops", "code", "identity", "Xoras_agent_cards", "tests",
               "workspaces", "data_center")
patterns = set()
evidence = []
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
            for lineno, line in enumerate(text.splitlines(), 1):
                if "misc/" not in line and "misc\\" not in line:
                    continue
                for token in re.findall(r"misc[/\\]([^\s\"'`(),;]+)", line):
                    name = Path(token).name
                    if not name or name in ("*", "."):
                        continue
                    patterns.add(name)
                    evidence.append({"file": str(p.relative_to(ROOT)), "line": lineno, "pattern": name})

restore_names = set()
for pat in patterns:
    if pat in by_name:
        restore_names.add(pat)
    elif any(ch in pat for ch in "*?["):
        restore_names.update(n for n in by_name if fnmatch.fnmatch(n, pat))

restored = []
failed = []
for name in sorted(restore_names):
    r = by_name[name]
    src = ROOT / r["destination"]
    dst = ROOT / r["source"]
    try:
        before = os.lstat(src)
        os.rename(src, dst)
        after = os.lstat(dst)
        ok = (after.st_ino == before.st_ino and after.st_size == before.st_size
              and after.st_mtime == before.st_mtime)
        if not ok:
            os.rename(dst, src)
            failed.append(name)
            continue
        restored.append(r)
    except OSError as exc:
        failed.append(f"{name}: {exc}")

kept = [r for r in records if Path(r["source"]).name not in restore_names]
manifest["files"] = kept
manifest["restored_live_referenced"] = restored
MANIFEST.write_text(json.dumps(manifest, indent=1))
manifest_hash = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()

summary["manifest_sha256"] = manifest_hash
summary["moved_files"] = len(kept)
summary["moved_bytes_apparent"] = sum(r["bytes"] for r in kept)
summary["restored_live_referenced_count"] = len(restored)
summary["restored_live_referenced"] = [r["source"] for r in restored[:20]]
summary["restore_failures"] = failed
by_cat = {}
bytes_by_cat = {}
for r in kept:
    by_cat[r["category"]] = by_cat.get(r["category"], 0) + 1
    bytes_by_cat[r["category"]] = bytes_by_cat.get(r["category"], 0) + r["bytes"]
summary["by_category"] = by_cat
summary["bytes_by_category"] = bytes_by_cat
summary["sha256_verified_files"] = sum(1 for r in kept if r["sha256"])
SUMMARY.write_text(json.dumps(summary, indent=2))

ledger = json.loads(LEDGER.read_text())
ledger.setdefault("resolved_not_moved", [])
if isinstance(ledger["resolved_not_moved"], list):
    ledger["resolved_not_moved"].append({
        "utc": summary["utc"],
        "kind": "LIVE_REFERENCED_PROVENANCE_OBJECTS_RESTORED",
        "item": f"{len(restored)} hhv_lattice provenance objects",
        "reason": "Active source in core/ops/provenance still cites misc/hhv_lattice*.rcgu.o as evidence; quarantine protocol forbids moving an item with live callers.",
        "source": "barn/archives/the_barn/misc_reorganize_20261124/object_files",
        "destination": "misc",
        "verification": f"{len(restored)} restored, {len(failed)} failures",
        "sha256": manifest_hash,
    })
LEDGER.write_text(json.dumps(ledger, indent=1))

print(json.dumps({"restore_names": len(restore_names), "restored": len(restored),
                  "failed": failed[:10], "kept": len(kept),
                  "evidence_examples": evidence[:5]}, indent=2))
