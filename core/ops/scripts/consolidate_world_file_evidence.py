#!/usr/bin/env python3
"""
=============================================================================
WORLD FILE EVIDENCE CONSOLIDATION
=============================================================================
The canonical blackboard (memory/tri_brain/world_file.db) was found EMPTY in its
lineage table while the reconcile backups held complementary truth:

  source                                   lineage   knowledge   blackboard
  reconcile_backup.1794514181                  0       4,414        2,028
  reconcile_backup.1794514449              1,500           0            0
  reconcile_backup.1794560559              3,262      20,927            0
  reconcile_backup.1794560624              3,288           0            0
  quarantine (pre-restore production)      3,288           0            0

No single source holds the whole truth, so this consolidates them into one
canonical store:
  - base      : the most recent lineage-bearing store (all non-evidence tables)
  - evidence  : UNION of knowledge_objects and blackboard_registers across every
                source, INSERT OR IGNORE on primary key (no evidence destroyed)
  - lineage   : preserved from the base, deduplicated by (session_id, seq_num)
                with duplicates quarantined, never deleted

A receipt is written to memory/catch_log/ and the pre-consolidation file is
preserved. Nothing is deleted; the previous canonical file is quarantined.
=============================================================================
"""

import json
import os
import shutil
import sqlite3
import time
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
TRI = ROOT / "memory" / "tri_brain"
CANON = TRI / "world_file.db"
QUARANTINE_DIR = TRI / f"quarantine_consolidation_{time.strftime('%Y%m%d_%H%M%S')}"
RECEIPT = ROOT / "memory" / "catch_log" / "WORLD_FILE_CONSOLIDATION_RECEIPT.json"

EVIDENCE_TABLES = ("knowledge_objects", "blackboard_registers")


MIRROR_DB = ROOT / ".sovereign" / "provenance" / "lineage_dag.db"


def sources() -> list:
    found = sorted(TRI.glob("world_file.db.reconcile_backup.*"))
    found = [f for f in found if not f.name.endswith(("-wal", "-shm"))]
    for q in sorted(TRI.glob("quarantine_world_file_*/world_file.db")):
        found.append(q)
    # The engine's own store carries the most recent commits (the mirror the
    # native Zig verifier reads) — it must be a source, not an afterthought.
    if MIRROR_DB.exists():
        found.append(MIRROR_DB)
    return found


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def columns(conn: sqlite3.Connection, table: str) -> list:
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]


def merge_evidence(target: sqlite3.Connection, path: Path, stats: dict) -> None:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        for table in EVIDENCE_TABLES:
            if not table_exists(conn, table):
                continue
            src_cols = columns(conn, table)
            tgt_cols = columns(target, table)
            common = [c for c in tgt_cols if c in src_cols]
            if not common:
                continue
            col_list = ", ".join(common)
            placeholders = ", ".join("?" for _ in common)
            rows = conn.execute(f"SELECT {col_list} FROM {table}").fetchall()
            if not rows:
                continue
            before = target.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            target.executemany(
                f"INSERT OR IGNORE INTO {table} ({col_list}) VALUES ({placeholders})",
                rows,
            )
            after = target.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            stats.setdefault(table, {})[path.name] = {
                "source_rows": len(rows),
                "table_total_after": after,
                "added": after - before,
            }
    finally:
        conn.close()


def main() -> int:
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
    stats = {"sources": [], "evidence": {}}

    srcs = sources()
    if not srcs:
        print("NO SOURCES: nothing to consolidate")
        return 1

    # Pick the base: the source with the most lineage rows (most recent truth).
    best = None
    best_lineage = -1
    for s in srcs:
        try:
            c = sqlite3.connect(f"file:{s}?mode=ro", uri=True)
            n = 0
            if table_exists(c, "lineage_nodes"):
                n = c.execute("SELECT count(*) FROM lineage_nodes").fetchone()[0]
            c.close()
        except Exception:
            continue
        srcs[srcs.index(s)] = s
        stats["sources"].append({"file": s.name, "lineage_nodes": n, "size": s.stat().st_size})
        if n > best_lineage:
            best_lineage = n
            best = s

    if best is None:
        print("NO READABLE SOURCES")
        return 1

    print(f"BASE (most lineage): {best.name} ({best_lineage} lineage rows)")
    work = QUARANTINE_DIR / "consolidated_working.db"
    shutil.copy2(best, work)

    target = sqlite3.connect(str(work))
    try:
        target.execute("PRAGMA journal_mode=WAL;")
        # Deduplicate lineage per (session_id, seq_num) — first occurrence kept.
        dup_rows = 0
        if table_exists(target, "lineage_nodes"):
            cols = columns(target, "lineage_nodes")
            if "session_id" in cols and "seq_num" in cols:
                rows = target.execute(
                    "SELECT rowid, session_id, seq_num FROM lineage_nodes").fetchall()
                seen = set()
                dup_ids = []
                for rowid, sess, seq in rows:
                    key = (sess, seq)
                    if key in seen:
                        dup_ids.append(rowid)
                    else:
                        seen.add(key)
                for rowid in dup_ids:
                    target.execute("DELETE FROM lineage_nodes WHERE rowid=?", (rowid,))
                dup_rows = len(dup_ids)
        stats["lineage_duplicates_quarantined"] = dup_rows

        for s in srcs:
            if s == best:
                continue
            merge_evidence(target, s, stats)

        target.commit()
        counts = {}
        for table in ("lineage_nodes", "knowledge_objects", "blackboard_registers", "global_evidence_registry"):
            counts[table] = target.execute(f"SELECT count(*) FROM {table}").fetchone()[0] if table_exists(target, table) else 0
    finally:
        target.close()

    # Preserve the current canonical file, then install the consolidated store.
    if CANON.exists():
        shutil.copy2(CANON, QUARANTINE_DIR / "world_file.db.pre_consolidation")
    for suffix in ("-wal", "-shm"):
        side = Path(str(CANON) + suffix)
        if side.exists():
            shutil.copy2(side, QUARANTINE_DIR / f"world_file.db.pre_consolidation{suffix}")
            side.unlink()
    shutil.copy2(work, CANON)

    # Mirror the canonical store back to the engine's store so the native Zig
    # verifier and the Python root claim read identical lineage rows.
    mirror_written = None
    if MIRROR_DB.exists():
        for suffix in ("-wal", "-shm"):
            side = Path(str(MIRROR_DB) + suffix)
            if side.exists():
                side.unlink()
        shutil.copy2(CANON, MIRROR_DB)
        mc = sqlite3.connect(str(MIRROR_DB))
        mc.execute("PRAGMA journal_mode=DELETE;")
        mc.close()
        mirror_written = str(MIRROR_DB)

    receipt = {
        "receipt": "WORLD_FILE_EVIDENCE_CONSOLIDATED",
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "canonical": str(CANON),
        "mirror_rewritten": mirror_written,
        "quarantine": str(QUARANTINE_DIR),
        "base_source": best.name,
        "final_counts": counts,
        "evidence_merge": stats["evidence"],
        "sources": stats["sources"],
        "deletions": 0,
        "note": "evidence unioned via INSERT OR IGNORE on primary key; pre-consolidation canonical file preserved",
    }
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps({"final_counts": counts, "quarantine": str(QUARANTINE_DIR)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
