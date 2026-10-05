#!/usr/bin/env python3
"""
=============================================================================
REFERENCE INTEGRITY CHECKER — SSOT Manifest Enforcement (Trust Gate)
=============================================================================
Governance: CATCH_LOG architecture / SSOT single-source-of-truth invariant
Purpose:  Software agents and humans keep referencing files that do not exist
          (phantom paths), or referencing stale-era absolute roots
          (Xoras_Workspace / Xoras_Sovereign_AI_Stack / Xoras_Project)
          instead of the canonical root. This tool:
            1. Builds a canonical FILE MANIFEST of every real tracked file
               (relative path + SHA-256) under the repo root.
            2. Scans all text sources for embedded file references
               (absolute Mac paths, markdown links, code imports/opens).
            3. Classifies every reference:
                 [RESOLVES]      -> target exists in manifest
                 [STALE-ROOT]    -> resolves after normalizing a legacy root
                                    (safe to auto-rewrite)
                 [PHANTOM]       -> points at a file that does not exist
                                    anywhere in the manifest (agent fiction)
                 [EXTERNAL]      -> points outside repo (legacy machine,
                                    ~/.gemini, other workspace roots)
            4. Exits non-zero if any PHANTOM references exist (fail-fast
               wake gate).
=============================================================================
"""

import argparse
import hashlib
import json
import os
import pathlib
import re
import sys
from collections import OrderedDict

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

CANONICAL_LEGACY_ROOTS = [
    "SSOT_Agentic_Brain",
    "Xoras_Workspace",
    "Xoras_Sovereign_AI_Stack",
    "Xoras_Project",
]

SKIP_PARTS = {".git", "__pycache__", "node_modules", "venv", ".venv"}
BINARY_EXT = {
    ".onnx", ".bin", ".dylib", ".pyc", ".jpg", ".png", ".wav", ".mp4", ".dmg",
    ".db", ".wal", ".o", ".exe", ".dll", ".so", ".a", ".img", ".zip", ".gz",
    ".out",
}
TEXT_EXT = {
    ".py", ".md", ".sh", ".json", ".yaml", ".yml", ".cpp", ".hpp", ".h",
    ".c", ".js", ".mjs", ".html", ".plist", ".txt", ".csv", ".jsonl",
    ".command", ".toml", ".cfg", ".lock",
}

EXT = "py|sh|json|yaml|yml|md|cpp|hpp|c|js|mjs|html|plist|txt|csv|jsonl|command|toml|cfg"
ABS_PATH_RE = re.compile(
    rf"""(?:file://)?/Users/[A-Za-z0-9_./\-]+\.(?:{EXT})(?!\w)"""
)
REL_PATH_RE = re.compile(
    rf"""(?<![\w/.-])((?:ops|ELITE_BOW|memory|data_center|capabilities|AI_Core|identity|workspaces|docs|assets)/[A-Za-z0-9_./\-]+\.(?:{EXT})(?!\w))"""
)
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^?#]+?)\)")
IMPORT_RE = re.compile(r"^\s*(?:import|from)\s+([A-Za-z0-9_\.]+)", re.M)
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^?#]+?)\)")


def build_manifest():
    manifest = OrderedDict()
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_PARTS for part in p.parts):
            continue
        rel = p.relative_to(ROOT).as_posix()
        if p.suffix.lower() in BINARY_EXT:
            continue
        try:
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
        except OSError:
            continue
        manifest[rel] = digest
    return manifest


def normalize_absolute(ref):
    """Return repo-relative path if ref targets canonical or a legacy root, else None."""
    for root_name in CANONICAL_LEGACY_ROOTS:
        marker = f"/Desktop/{root_name}/"
        idx = ref.find(marker)
        if idx >= 0:
            return ref[idx + len(marker):], root_name
    return None, None


def resolve(rel_candidate, src_rel, manifest):
    cands = [
        rel_candidate,
        os.path.normpath(os.path.join(os.path.dirname(src_rel), rel_candidate)).replace("\\", "/"),
    ]
    for c in cands:
        c = c.lstrip("./").lstrip("/")
        if c in manifest:
            return c
    return None


def main():
    ap = argparse.ArgumentParser(description="SSOT reference-integrity trust gate")
    ap.add_argument("--root", default=str(ROOT), help="repo root (default: this repo)")
    ap.add_argument("--manifest-out", default=str(ROOT / "ops" / "config" / "file_manifest.json"),
                    help="where to write the canonical manifest")
    ap.add_argument("--report", default=str(ROOT / "ops" / "discernment" / "reports" / "REFERENCE_INTEGRITY_REPORT.json"),
                    help="where to write the full classification report")
    ap.add_argument("--write-manifest", action="store_true",
                    help="persist manifest and per-file reference map (default: read-only)")
    args = ap.parse_args()

    root = pathlib.Path(args.root).resolve()
    manifest = build_manifest()
    print(f"[REF-INTEGRITY] canonical manifest: {len(manifest)} real text files under {root}")

    stats = OrderedDict((k, 0) for k in ("resolves", "stale_root", "phantom", "external"))
    phantom_by_path = OrderedDict()
    stale_by_path = OrderedDict()
    source_map = OrderedDict()

    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_PARTS for part in p.parts):
            continue
        if p.suffix.lower() in BINARY_EXT or p.suffix.lower() not in TEXT_EXT:
            continue
        src_rel = p.relative_to(root).as_posix()
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        found = set()
        for m in ABS_PATH_RE.finditer(text):
            found.add(m.group(0).replace("file://", ""))
        for m in REL_PATH_RE.finditer(text):
            found.add(m.group(1))
        for m in MD_LINK_RE.finditer(text):
            link = m.group(1).strip()
            if link.startswith(("http", "#", "mailto:", "file:/")) or "/" not in link:
                continue
            found.add(link)
        for m in IMPORT_RE.finditer(text):
            mod = m.group(1).split(".")[0]
            if not (mod.startswith("xoras") or mod in ("sentinel_core", "voice_service", "omni_ingestor")):
                continue
            target = mod + ".py"
            if target not in manifest:
                hits = [key for key in manifest if key.endswith("/" + target)]
                # treat import as a reference even if module located deeper (e.g. Source/)
                if hits:
                    found.add(hits[0])
                else:
                    found.add(target)

        for ref in sorted(found):
            ref = ref.strip()
            if not ref or len(ref) < 4:
                continue

            rel_candidate, legacy = normalize_absolute(ref)
            if rel_candidate is None:
                # already-relative or non-repo absolute
                rel_candidate = ref

            hit = resolve(rel_candidate, src_rel, manifest)

            if hit:
                stats["resolves"] += 1
                source_map.setdefault(hit, []).append(src_rel)
            elif legacy and rel_candidate:
                stats["stale_root"] += 1
                stale_by_path.setdefault(rel_candidate, set()).add(src_rel)
            elif ref.startswith("/Users/") or ref.startswith("C:\\") or ref.startswith("/"):
                stats["external"] += 1
            else:
                stats["phantom"] += 1
                phantom_by_path.setdefault(rel_candidate, set()).add(src_rel)

    print(f"[REF-INTEGRITY] classification (per reference token):")
    for k, v in stats.items():
        print(f"    {k:>10}: {v}")

    print("\n[PHANTOM] references to files that do NOT exist on disk (agent fiction):")
    if phantom_by_path:
        for path, srcs in sorted(phantom_by_path.items(), key=lambda kv: -len(kv[1])):
            print(f"    MISSING  {path}  <= {len(srcs)} ref")
    else:
        print("    none — clean")

    print("\n[STALE-ROOT] references that resolve only after normalizing a legacy root:")
    for path, srcs in sorted(stale_by_path.items(), key=lambda kv: -len(kv[1])):
        print(f"    FIXABLE  {path}  <= {len(srcs)} ref")

    if args.write_manifest:
        manifest_path = pathlib.Path(args.manifest_out)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"\n[wrote] canonical manifest -> {manifest_path}")

    report_path = pathlib.Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "root": str(root),
        "manifest_file_count": len(manifest),
        "classification": dict(stats),
        "phantom:pretty".split(":")[0]: {
            k: sorted(v) for k, v in phantom_by_path.items()
        },
        "stale_root_fixable": {k: sorted(v) for k, v in stale_by_path.items()},
        "referenced_real_files": {
            k: sorted(set(v))[:25] for k, v in source_map.items()
        },
    }
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"[wrote] full report -> {report_path}")

    # Fail-fast gate: non-zero exit if any phantom reference exists.
    if phantom_by_path:
        print(f"\n[GATE] FAIL — {len(phantom_by_path)} phantom reference(s). "
              f"No file/agent may claim a path that is not in the manifest.")
        sys.exit(1)
    print("\n[GATE] PASS — every reference resolves to a real file.")


if __name__ == "__main__":
    main()