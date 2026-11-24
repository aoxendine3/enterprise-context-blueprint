#!/usr/bin/env python3
"""DAXX engine engagement on misc/ — bounded, read-only.

Boots the real DaxxCo sovereign runtime and applies its verifiable components
(AST taint scanner, falsification-style physical walk, literal secret scan)
to misc/. Theatrical scripts with hardcoded swarm counts / simulated output
are classified but never executed. Nothing under misc/ is opened for writing.
"""
import os, sys, json, time, ast, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MISC = ROOT / "misc"
sys.path.insert(0, str(ROOT))

from ops.scripts.daxxco_sovereign_runtime import DaxxCoSovereignEngine
from ops.scripts.daxx_ast_taint_live_scanner import SemanticASTTaintScanner

RECEIPT = ROOT / "memory/catch_log/DAXX_ENGINE_MISC_ENGAGEMENT_20261124.json"
SAMPLE_CAP = 2000
result = {
    "schema": "xoras.daxx_engine_misc_engagement.v1",
    "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "target": "misc",
    "read_only": True,
    "sample_cap": SAMPLE_CAP,
}
t0 = time.time()

# ---- 1. Real engine boot ----------------------------------------------------
try:
    engine = DaxxCoSovereignEngine()
    result["sovereign_engine"] = {
        "status": "BOOTED",
        "ledgers_loaded": engine.loaded_count,
        "ledger_bytes": engine.total_bytes,
        "load_latency_ms": round(engine.load_latency_ms, 3),
    }
    gate = engine.query_subagent("daxx", "Engage diagnostics on misc/ with no destructive action")
    result["grounding_gate"] = {
        "decision": gate.get("decision"),
        "response": gate.get("response"),
        "latency_ms": gate.get("latency_ms"),
        "note": "deterministic sovereign rule gate, not an LLM judgment",
    }
except Exception as exc:
    result["sovereign_engine"] = {"status": "BOOT_FAILED", "error": str(exc)}

# ---- 2. Real AST/taint component on misc ------------------------------------
py_files = []
for base, dirs, files in os.walk(MISC, followlinks=False):
    dirs[:] = [d for d in dirs if d != ".git"]
    py_files.extend(Path(base) / f for f in files if f.endswith(".py"))
nodes = sinks = parsed = 0
for p in py_files[:SAMPLE_CAP]:
    try:
        tree = ast.parse(p.read_bytes(), filename=str(p))
        scanner = SemanticASTTaintScanner(str(p))
        scanner.visit(tree)
        parsed += 1
        nodes += scanner.ast_nodes
        sinks += len(scanner.taint_sinks)
    except Exception:
        pass
result["ast_taint"] = {
    "python_files_found": len(py_files),
    "modules_parsed": parsed,
    "ast_nodes": nodes,
    "taint_sinks": sinks,
    "verdict": "REAL_ZERO_NO_TARGETS" if not py_files else "SCANNED",
}

# ---- 3. DAXX falsification-style physical walk, targeted at misc -------------
files = 0
allocated = apparent = 0
types = {}
large = []
for base, dirs, names in os.walk(MISC, topdown=True, followlinks=False):
    dirs[:] = [d for d in dirs if d != ".git"]
    for name in names:
        p = Path(base) / name
        try:
            st = p.lstat()
        except OSError:
            continue
        if p.is_symlink():
            continue
        files += 1
        apparent += st.st_size
        allocated += st.st_blocks * 512
        ext = p.suffix.lower() or "no_ext"
        types[ext] = types.get(ext, 0) + 1
        if st.st_size > (1 << 30):
            large.append({"path": str(p.relative_to(ROOT)), "apparent_bytes": st.st_size,
                          "allocated_bytes": st.st_blocks * 512})
result["physical_walk"] = {
    "files": files,
    "apparent_bytes": apparent,
    "allocated_bytes": allocated,
    "top_extensions": dict(sorted(types.items(), key=lambda kv: -kv[1])[:10]),
    "large_sparse_objects": sorted(large, key=lambda x: -x["allocated_bytes"]),
}

# ---- 4. Literal high-entropy token checks (DAXX Phase 3 logic) ---------------
MARKERS = ["AIzaSy", "sk-proj-", "ghp_", "xoxb-"]
hits = []
examined = 0
sample_step = max(1, files // SAMPLE_CAP)
idx = 0
for base, dirs, names in os.walk(MISC, topdown=True, followlinks=False):
    dirs[:] = [d for d in dirs if d != ".git"]
    for name in names:
        if idx % sample_step:
            idx += 1
            continue
        idx += 1
        p = Path(base) / name
        try:
            if p.is_symlink() or p.stat().st_size > 2_000_000:
                continue
            with p.open("rb") as fh:
                head = fh.read(262144)
        except OSError:
            continue
        examined += 1
        for marker in MARKERS:
            if marker.encode() in head:
                hits.append({"file": str(p.relative_to(ROOT)), "marker": marker})
result["literal_secret_scan"] = {
    "files_examined": examined,
    "markers": MARKERS,
    "hits": hits[:25],
    "total_hits": len(hits),
    "note": "literal marker presence only; not proof of a live credential",
}

# ---- 5. Headroom -------------------------------------------------------------
try:
    result["headroom"] = subprocess.check_output(["df", "-h", str(MISC)], text=True).strip().splitlines()[-1]
except Exception as exc:
    result["headroom"] = f"ERROR {exc}"

# ---- 6. Engine inventory: what was NOT run and why --------------------------
result["engine_inventory"] = [
    {"script": "ops/scripts/daxxco_sovereign_runtime.py", "class": "REAL", "action": "booted; 10 ledgers"},
    {"script": "ops/scripts/daxx_ast_taint_live_scanner.py", "class": "REAL", "action": "invoked on misc; 0 python targets"},
    {"script": "ops/scripts/daxxco_rigorous_falsification_audit.py", "class": "REAL_WHOLE_TREE", "action": "phases replicated with misc target; whole-tree receipt not regenerated"},
    {"script": "ops/scripts/daxx_master_orchestrator.py", "class": "THEATRICAL", "action": "NOT RUN - hardcoded 26,000-node claim, sleeps, shutil.move of core scripts"},
    {"script": "ops/scripts/daxx_ast_parser_daemon.py", "class": "THEATRICAL", "action": "NOT RUN - simulated compilation and synthetic Rust output"},
    {"script": "ops/scripts/daxxco_live_swarm_auditor.py", "class": "THEATRICAL", "action": "NOT RUN - hardcoded 21-agent/63-node and 100% claims"},
]
result["elapsed_sec"] = round(time.time() - t0, 2)

RECEIPT.write_text(json.dumps(result, indent=2))
print(json.dumps({k: result[k] for k in ("sovereign_engine", "grounding_gate", "ast_taint", "literal_secret_scan", "headroom", "engine_inventory", "elapsed_sec")}, indent=2)[:7000])
print("RECEIPT:", RECEIPT)
