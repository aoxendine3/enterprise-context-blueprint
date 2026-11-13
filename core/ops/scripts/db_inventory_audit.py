#!/usr/bin/env python3
#=============================================================================
# DB INVENTORY & TIMELINE AUDITOR — CANONICAL CATALOG OF ALL DATABASES
#=============================================================================
# Governance: user mandate — "auditing all db we have, sync the data so we
# know what is what, timeline and history."
#
# What this does:
#   1. Discovers every SQLite database in the SSOT (barn/ excluded per
#      Log Entry #080 — banned reading zone).
#   2. For each DB: size, mtime, integrity_check (read-only), journal_mode,
#      tables + row counts, lineage timeline (earliest/latest node timestamp,
#      session count).
#   3. Classifies each DB's role (canonical store, mirror, test, backup,
#      adversarial fixture) and cross-checks canonical vs mirror consistency.
#   4. SYNCS the result into:
#        memory/intelligence/db_catalog.json   (full current snapshot)
#        memory/intelligence/db_catalog_timeline.jsonl (append-only history)
#        memory/catch_log/db_inventory_audit.log (receipt)
#
# Fail-closed: any DB that cannot be opened read-only is recorded as
# UNREADABLE with the reason — never skipped silently.
#=============================================================================
import datetime
import hashlib
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
OUT_JSON = ROOT / "memory/intelligence/db_catalog.json"
OUT_JSONL = ROOT / "memory/intelligence/db_catalog_timeline.jsonl"
OUT_LOG = ROOT / "memory/catch_log/db_inventory_audit.log"

SCAN_DIRS = ["memory", ".sovereign", "core", "workspaces", "docs", "scripts", "tests", "ops"]
EXCLUDE_PARTS = {"barn", "__pycache__", "node_modules", ".git"}

ROLE_RULES = [
    ("memory/tri_brain/world_file.db", "CANONICAL_EVIDENCE_STORE"),
    (".sovereign/provenance/lineage_dag.db", "LINEAGE_MIRROR"),
    ("memory/tri_brain/merkle", "MERKELE_ROOT_ZONE"),
]


def classify(rel: str) -> str:
    p = rel.lower()
    if rel == "memory/tri_brain/world_file.db":
        return "CANONICAL_EVIDENCE_STORE"
    if rel == ".sovereign/provenance/lineage_dag.db":
        return "LINEAGE_MIRROR"
    if "reconcile_backup" in p:
        return "PRE_RECONCILE_BACKUP"
    if any(k in p for k in ("backup", "snapshot", "bak")):
        return "BACKUP"
    if any(k in p for k in ("test", "corrupt", "adversarial", "break_", "fixture", "demo", "sample")):
        return "TEST_OR_ADVERSARIAL_FIXTURE"
    if any(k in p for k in ("benchmark", "bench")):
        return "BENCHMARK_EVIDENCE"
    if p.startswith("memory/tri_brain"):
        return "TRI_BRAIN_GOVERNANCE"
    if p.startswith(".sovereign/provenance"):
        return "PROVENANCE_ZONE"
    if p.startswith("memory/"):
        return "MEMORY_ZONE"
    return "UNCORROBORATED_ROLE"


def discover_dbs():
    found = []
    seen = set()
    for d in SCAN_DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [x for x in dirnames if x not in EXCLUDE_PARTS]
            for fn in filenames:
                p = Path(dirpath) / fn
                if fn.endswith(("-wal", "-shm")) or fn.startswith("._"):
                    continue
                if not (fn.endswith(".db") or fn.endswith(".sqlite") or fn.endswith(".sqlite3")):
                    continue
                rel = str(p.relative_to(ROOT))
                if rel in seen:
                    continue
                seen.add(rel)
                found.append(p)
    return sorted(found)


def audit_db(p: Path) -> dict:
    rel = str(p.relative_to(ROOT))
    st = p.stat()
    rec = {
        "path": rel,
        "role": classify(rel),
        "bytes": st.st_size,
        "mtime_utc": datetime.datetime.utcfromtimestamp(st.st_mtime).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sha256_head": None,
        "status": "OK",
        "journal_mode": None,
        "integrity": None,
        "tables": {},
        "timeline": None,
    }
    try:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            head = f.read(1 << 16)
            h.update(head)
        rec["sha256_head"] = h.hexdigest()[:16]
        conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True, timeout=5)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        try:
            rec["journal_mode"] = cur.execute("PRAGMA journal_mode").fetchone()[0]
        except Exception:
            rec["journal_mode"] = "unknown"
        try:
            rec["integrity"] = cur.execute("PRAGMA quick_check").fetchone()[0]
        except Exception as e:
            rec["integrity"] = f"error: {e}"
        tables = [r[0] for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
        total_rows = 0
        for t in tables:
            try:
                n = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
            except Exception as e:
                n = f"error: {e}"
            rec["tables"][t] = n
            if isinstance(n, int):
                total_rows += n
        rec["total_rows"] = total_rows

        # Timeline: lineage-ish tables with timestamp columns
        for t in tables:
            if not any(k in t.lower() for k in ("lineage", "node", "checkpoint", "event")):
                continue
            try:
                cols = [r[1] for r in cur.execute(f'PRAGMA table_info("{t}")').fetchall()]
                ts_col = next((c for c in ("timestamp", "ts", "created_at") if c in cols), None)
                if ts_col is None:
                    continue
                row = cur.execute(
                    f'SELECT MIN("{ts_col}"), MAX("{ts_col}"), COUNT(*) FROM "{t}"').fetchone()
                if row and row[2]:
                    rec["timeline"] = {
                        "table": t,
                        "earliest": str(row[0]),
                        "latest": str(row[1]),
                        "rows": row[2],
                    }
                    break
            except Exception:
                continue

        # Session diversity for lineage_nodes
        if "lineage_nodes" in tables:
            try:
                rec["sessions"] = cur.execute(
                    "SELECT COUNT(DISTINCT session_id) FROM lineage_nodes").fetchone()[0]
            except Exception:
                pass
        conn.close()
    except Exception as e:
        rec["status"] = "UNREADABLE"
        rec["error"] = str(e)
    return rec


def crosscheck(records):
    cc = {}
    by_path = {r["path"]: r for r in records}
    wf = by_path.get("memory/tri_brain/world_file.db")
    ld = by_path.get(".sovereign/provenance/lineage_dag.db")
    if wf and ld and isinstance(wf["tables"].get("lineage_nodes"), int) and isinstance(ld["tables"].get("lineage_nodes"), int):
        cc["canonical_vs_mirror_nodes"] = {
            "world_file.db": wf["tables"]["lineage_nodes"],
            "lineage_dag.db": ld["tables"]["lineage_nodes"],
            "in_sync": wf["tables"]["lineage_nodes"] == ld["tables"]["lineage_nodes"],
        }
    return cc


def main():
    t0 = time.time()
    dbs = discover_dbs()
    records = [audit_db(p) for p in dbs]
    crosschecks = crosscheck(records)
    run = {
        "run_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "db_count": len(records),
        "unreadable": sum(1 for r in records if r["status"] != "OK"),
        "crosschecks": crosschecks,
        "databases": records,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(run, indent=2, sort_keys=True), encoding="utf-8")
    with open(OUT_JSONL, "a", encoding="utf-8") as fh:
        summary = {
            "run_utc": run["run_utc"],
            "db_count": run["db_count"],
            "unreadable": run["unreadable"],
            "crosschecks": crosschecks,
            "catalog_sha256": hashlib.sha256(
                json.dumps(run, sort_keys=True).encode()).hexdigest(),
        }
        fh.write(json.dumps(summary, sort_keys=True) + "\n")
    lines = [
        f"[{run['run_utc']}] DB INVENTORY AUDIT: {run['db_count']} databases audited, "
        f"{run['unreadable']} unreadable, elapsed {time.time()-t0:.1f}s",
        f"  catalog: {OUT_JSON}",
        f"  timeline history appended: {OUT_JSONL}",
    ]
    for k, v in crosschecks.items():
        lines.append(f"  crosscheck {k}: {v}")
    for r in records:
        if r["status"] != "OK":
            lines.append(f"  UNREADABLE: {r['path']} ({r.get('error')})")
    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_LOG, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"OK: catalog synced ({len(records)} DBs)")


if __name__ == "__main__":
    main()
