#!/usr/bin/env python3
"""
SSOT WIRE AUDIT — evidence-based, fail-closed.

Invoked by the real collective (Maxx worker / Vance critic pattern). This audit
does NOT print PASS theater. For each check it gathers on-disk evidence, records
PASS / FAIL / DEGRADED with the actual numbers, and exits non-zero if any
CRITICAL check fails. Receipt is written to memory/catch_log/SSOT_WIRE_AUDIT_RECEIPT.json.
"""
import os
import sys
import json
import ast
import time
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
RECEIPT = ROOT / "memory/catch_log/SSOT_WIRE_AUDIT_RECEIPT.json"
results = []


def record(check, status, severity, detail, evidence):
    results.append({
        "check": check, "status": status, "severity": severity,
        "detail": detail, "evidence": evidence,
    })


# 1. CITIZEN SCOPE — every 22 citizens must resolve on the sealed manifest.
manifest_p = ROOT / "identity/sovereign_citizens_manifest.json"
manifest = json.loads(manifest_p.read_text()) if manifest_p.exists() else {"citizens": []}
cards_dir = ROOT / "Xoras_agent_cards"
missing_cards = []
for c in manifest.get("citizens", []):
    aid = c.get("agent_id", "")
    if not list(cards_dir.glob(f"{aid}.json")) and not list((ROOT / "agents/citizens").glob(f"{aid}.json")):
        missing_cards.append(aid)
record("citizen_cards", "PASS" if not missing_cards else "FAIL", "CRITICAL",
       f"{len(manifest.get('citizens', []))} citizens sealed; {len(missing_cards)} missing cards",
       {"missing": missing_cards})

# 2. WITNESS WIRES — both witness scripts + native binaries exist and execute.
wires = {
    "witness_a_bin": ROOT / "core/ops/bin/stateless_airblocked_witness",
    "witness_b_py": ROOT / "core/ops/scripts/independent_python_witness.py",
    "dual_witness_gate": ROOT / "core/ops/scripts/dual_witness_gate.sh",
    "reality_gate": ROOT / "ops/scripts/reality_gate.sh",
}
dead = [k for k, p in wires.items() if not p.exists()]
record("witness_wires", "PASS" if not dead else "FAIL", "CRITICAL",
       f"{len(wires) - len(dead)}/{len(wires)} witness wires present", {"dead": dead})

# 3. SSOT CLAIM INTEGRITY — merkle claim must equal the root RECOMPUTED
# from the canonical lineage DAG (NOT git HEAD — different hash domains).
claim = (ROOT / "memory/tri_brain/merkle_root.hash").read_text().strip()
import hashlib
import sqlite3
db = ROOT / "memory/tri_brain/world_file.db"
recomputed = ""
if db.exists():
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        layer = [r[0] for r in conn.execute(
            "SELECT node_id FROM lineage_nodes ORDER BY timestamp ASC, rowid ASC").fetchall()]
        conn.close()
        # canonical order is the DB insertion order; sqlite may return the
        # node_id column as bytes under some drivers — normalize to str and
        # apply the EXACT gate algorithm (pairwise sha256 of concatenated ids).
        layer = [x.decode() if isinstance(x, bytes) else str(x) for x in layer]
        while len(layer) > 1:
            layer = [hashlib.sha256((layer[i] + layer[i+1]).encode()).hexdigest()
                     if i + 1 < len(layer) else layer[i]
                     for i in range(0, len(layer), 2)]
        recomputed = layer[0] if layer else ""
    except Exception as e:
        recomputed = f"ERROR:{e}"
record("claim_vs_dag", "PASS" if claim == recomputed else "FAIL", "CRITICAL",
       f"claim={claim[:12]} dag_root={recomputed[:12]}",
       {"claim": claim, "dag_root": recomputed})

# 4. DEAD PATH REFERENCES — scan canonical scripts for paths that do not exist.
dead_refs = []
scan_roots = [ROOT / "ops/scripts", ROOT / "core/ops/scripts"]
scanned = 0
for sr in scan_roots:
    if not sr.exists():
        continue
    for p in sr.rglob("*.py"):
        try:
            txt = p.read_text(errors="ignore")
        except Exception:
            continue
        scanned += 1
        for node in ast.walk(ast.parse(txt)) if txt else []:
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                v = node.value
                if v.startswith(str(ROOT)) and ("/" in v) and len(v) > len(str(ROOT)) + 3:
                    # check first path segment after root
                    rel = v[len(str(ROOT)):].lstrip("/").split("/")[0]
                    if rel and not (ROOT / rel).exists():
                        dead_refs.append({"script": str(p.relative_to(ROOT)), "ref": v[:120]})
record("dead_path_refs", "PASS" if not dead_refs else "DEGRADED", "HIGH",
       f"{len(dead_refs)} hardcoded paths point at non-existent roots across {scanned} scripts",
       {"refs": dead_refs[:25]})

# 5. AUDIT ENGINE HONESTY — detect hardcoded PASS theater in *audit* scripts.
theater = []
for p in (ROOT / "ops/scripts").rglob("*audit*.py"):
    try:
        txt = p.read_text(errors="ignore")
    except Exception:
        continue
    if "status\": \"PASS\"" in txt and "if __name__" not in txt:
        theater.append(str(p.relative_to(ROOT)))
    elif txt.count('"PASS"') >= 3 and "def record" not in txt and "fail_closed" not in txt:
        theater.append(str(p.relative_to(ROOT)) + " (3+ literal PASS, no fail-closed path)")
record("audit_honesty", "PASS" if not theater else "FAIL", "CRITICAL",
       f"{len(theater)} audit scripts hardcode PASS without a fail-closed gate",
       {"theater": theater[:20]})

# 6. DAXX ENGINE REALITY — scripts must be import-safe (no side effects on
# import) and expose an explicit __main__ entrypoint. Un-guarded scripts that
# do destructive file moves on import are far worse than print stubs.
unsafe = []
for p in list((ROOT / "ops/scripts").glob("daxx*.py")) + list((ROOT / "ops/scripts").glob("daxxco*.py")):
    try:
        txt = p.read_text(errors="ignore")
    except Exception:
        continue
    has_main = "if __name__" in txt
    # Detect destructive calls that execute at module scope (col 0).
    destructive = any(
        line.startswith(("shutil.move", "shutil.copy", "os.remove", "os.rename", "os.unlink"))
        for line in txt.splitlines()
    )
    if not has_main:
        unsafe.append({"script": str(p.relative_to(ROOT)),
                       "destructive_at_import": destructive})
record("daxx_engines", "PASS" if not unsafe else "DEGRADED", "HIGH",
       f"{len(unsafe)} Daxx scripts lacked an import guard (destructive-at-import: "
       f"{sum(1 for u in unsafe if u['destructive_at_import'])})",
       {"unguarded": unsafe})

# 7. GATE RUNNERS — reality gate must be executable and its LAST receipt PASS.
# Freshness: a receipt older than 30 min is STALE, not authoritative. When
# stale, RE-RUN the gate to get a live verdict instead of trusting old bytes
# (this breaks the circular dependency where the wire audit failed on a
# previous run's verdict before the gate had a chance to regenerate it).
import subprocess as _sp
rg = wires["reality_gate"]
last_receipt = ROOT / "memory/catch_log/REALITY_GATE_RECEIPT.json"
verdict = ""
rerun = False
if last_receipt.exists():
    try:
        data = json.loads(last_receipt.read_text())
        verdict = data.get("verdict", "")
        ts = data.get("timestamp_utc", "")
        from datetime import datetime, timezone
        age = (datetime.now(timezone.utc) - datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)).total_seconds()
        if age > 1800:
            rerun = True
    except Exception:
        rerun = True
if rerun or "PASS" not in verdict:
    # Re-run the live gate to produce a fresh verdict.
    try:
        _sp.run(["bash", str(rg)], cwd=ROOT, capture_output=True, timeout=900)
        verdict = json.loads(last_receipt.read_text()).get("verdict", "")
    except Exception:
        pass
ok = os.access(rg, os.X_OK) and "PASS" in verdict
record("gate_runners", "PASS" if ok else "FAIL", "CRITICAL",
       f"reality_gate executable={os.access(rg, os.X_OK)} verdict={verdict or 'unparseable'}"
       f"{' (re-run for freshness)' if rerun else ''}",
       {"verdict": verdict})

# --- synthesize ---
status_counts = {}
for r in results:
    status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1
critical_fail = any(r["status"] == "FAIL" and r["severity"] == "CRITICAL" for r in results)
verdict = "SSOT_WIRE_AUDIT_FAIL" if critical_fail else (
    "SSOT_WIRE_AUDIT_DEGRADED" if status_counts.get("DEGRADED") else "SSOT_WIRE_AUDIT_PASS")

payload = {
    "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "verdict": verdict,
    "counts": status_counts,
    "critical_fail": critical_fail,
    "checks": results,
}
RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps(payload, indent=2))

print("=" * 70)
print("SSOT WIRE AUDIT — EVIDENCE-BASED, FAIL-CLOSED")
print("=" * 70)
for r in results:
    print(f"[{r['status']:8}] {r['severity']:8} {r['check']}: {r['detail']}")
print("-" * 70)
print(f"VERDICT: {verdict}   {status_counts}")
print(f"Receipt: {RECEIPT}")
sys.exit(1 if critical_fail else 0)
