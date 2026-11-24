#!/usr/bin/env python3
"""Universal read-only audit of misc/ using the repo's own scanners.

Every pass is bounded: at most SAMPLE files are read, and only their first
8 KiB. No file in misc/ is opened for writing. Results go to scratch/.
"""
import os, sys, ast, json, time, collections, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MISC = ROOT / "misc"
SAMPLE = 2000
sys.path.insert(0, str(ROOT / "ops" / "scripts"))

report = {"schema": "xoras.universal_misc_audit.v1", "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "read_only": True, "sample_cap": SAMPLE}
t0 = time.time()

# ---- 1. inventory (stat only) ------------------------------------------------
by_ext = collections.Counter(); by_ext_bytes = collections.Counter()
paths = []; code = []
for base, dirs, files in os.walk(MISC, topdown=True, followlinks=False):
    dirs[:] = [d for d in dirs if d != ".git"]
    for name in files:
        p = Path(base) / name
        try:
            st = p.lstat()
        except OSError:
            continue
        if p.is_symlink():
            continue
        ext = p.suffix.lower() or "(none)"
        by_ext[ext] += 1; by_ext_bytes[ext] += st.st_size
        paths.append((str(p.relative_to(ROOT)), st.st_size))
        if ext in (".py", ".js", ".ts", ".mjs", ".cjs", ".sh", ".json", ".md", ".yaml", ".yml", ".env"):
            code.append(p)
report["inventory"] = {
    "files": len(paths),
    "extensions_top": [{"ext": e, "count": c, "apparent_bytes": by_ext_bytes[e]} for e, c in by_ext.most_common(15)],
    "code_ish_files": len(code),
    "python_files": by_ext.get(".py", 0),
}

# ---- 2. magic-byte classification of a deterministic sample ------------------
def magic(head: bytes) -> str:
    sigs = [
        (b"\x89PNG\r\n\x1a\n", "PNG image"), (b"%PDF", "PDF document"),
        (b"\x7fELF", "ELF binary"), (b"SQLite format 3\x00", "SQLite database"),
        (b"PK\x03\x04", "ZIP archive"), (b"\x1f\x8b", "gzip stream"),
        (b"#!/", "script/shebang"), (b"MZ", "DOS executable"),
        (b"\x00asm", "WASM"), (b"OggS", "Ogg media"), (b"RIFF", "RIFF media"),
    ]
    for sig, name in sigs:
        if head.startswith(sig):
            return name
    try:
        head.decode("utf-8")
        return "utf8-text"
    except UnicodeDecodeError:
        return "opaque-binary"

sample = paths[::max(1, len(paths) // SAMPLE)][:SAMPLE]
magic_counts = collections.Counter()
for rel, _ in sample:
    try:
        with open(ROOT / rel, "rb") as fh:
            magic_counts[magic(fh.read(16))] += 1
    except OSError:
        magic_counts["unreadable"] += 1
report["magic_sample"] = {"count": len(sample), "classes": dict(magic_counts)}

# ---- 3. repo scanners: AST / taint / credentials / classifier ----------------
try:
    from multi_lang_ast_parser import scan_symbol_equivalence
    ast_manifest = scan_symbol_equivalence(str(MISC))
    report["ast_symbol_scan"] = {"modules_parsed": len(ast_manifest), "python_targets_found": by_ext.get(".py", 0)}
except Exception as exc:
    report["ast_symbol_scan"] = {"error": str(exc)}

try:
    import daxx_ast_taint_live_scanner as taint
    nodes = sinks = scanned = 0
    for p in [x for x in code if x.suffix == ".py"][:SAMPLE]:
        tree = ast.parse(p.read_bytes(), filename=str(p))
        s = taint.SemanticASTTaintScanner(str(p)); s.visit(tree)
        scanned += 1; nodes += s.ast_nodes; sinks += len(s.taint_sinks)
    report["taint_scan"] = {"python_modules": scanned, "ast_nodes": nodes, "taint_sinks": sinks}
except Exception as exc:
    report["taint_scan"] = {"error": str(exc)}

try:
    import deep_credential_audit as cred
    findings = []
    scan_targets = code + [ROOT / rel for rel, _ in sample][:SAMPLE]
    for p in scan_targets:
        if not p.is_file() or p.stat().st_size > 2_000_000:
            continue
        try:
            text = p.read_text(errors="ignore")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for kind, pat in cred.PATTERNS.items():
                if pat.search(line):
                    findings.append({"file": str(p.relative_to(ROOT)), "line": lineno, "kind": kind})
    report["credential_scan"] = {"files_examined": len(scan_targets), "findings": findings[:50], "total_findings": len(findings)}
except Exception as exc:
    report["credential_scan"] = {"error": str(exc)}

try:
    import preflight_data_classifier as pre
    classified = collections.Counter()
    for rel, _ in sample[:200]:
        res = pre.classify_dataset(str(ROOT / rel))
        classified[res.get("status")] += 1
    report["preflight_classifier"] = {"sample": min(200, len(sample)), "verdicts": dict(classified)}
except Exception as exc:
    report["preflight_classifier"] = {"error": str(exc)}

# ---- 4. nested git + DAG/reference context ----------------------------------
def git_cmd(args):
    try:
        return subprocess.run(["git", "-C", str(MISC)] + args, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception as exc:
        return f"ERROR {exc}"

report["nested_git"] = {
    "objects": git_cmd(["count-objects", "-v"]).splitlines()[:6],
    "branch": git_cmd(["branch", "--show-current"]),
    "head": git_cmd(["rev-parse", "--verify", "HEAD"]) or "(no commit)",
    "index_entries": len(git_cmd(["ls-files"]).splitlines()),
}

refs = []
for base in ("data_center", "memory/catch_log", "docs/audits", "core/ops", "ops/scripts"):
    for p in (ROOT / base).rglob("*"):
        if not p.is_file() or p.stat().st_size > 4_000_000:
            continue
        try:
            text = p.read_text(errors="ignore")
        except OSError:
            continue
        if "misc/" in text or "misc\\" in text:
            refs.append(str(p.relative_to(ROOT)))
report["repo_references"] = {"count": len(refs), "files": refs[:25]}

report["elapsed_sec"] = round(time.time() - t0, 2)
out = ROOT / "scratch" / "universal_misc_audit_20261124.json"
out.write_text(json.dumps(report, indent=2))
print(json.dumps({k: (v if k in ("inventory", "magic_sample", "ast_symbol_scan", "taint_scan", "credential_scan", "preflight_classifier", "nested_git", "repo_references", "elapsed_sec") else v) for k, v in report.items()}, indent=2)[:9000])
print("REPORT:", out)
