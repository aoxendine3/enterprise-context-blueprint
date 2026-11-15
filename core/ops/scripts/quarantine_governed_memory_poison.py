#!/usr/bin/env python3
"""
Quarantine poisoned governed-memory rows — preserve, prove, report
==================================================================

The live governance database accepted signed semantic poison before the
Poincaré gate was wired into the write path. Those rows are still marked
``ACCEPTED``, so any harness that reads the database sees the poison as
canonical.

This script does not delete them. It:

1. takes a byte-identical backup of the database and records its SHA-256,
2. copies each poisoned row into ``memory_records_quarantine``,
3. marks the original row ``QUARANTINED`` with a timestamp and reason,
4. appends an entry to ``memory/catch_log/QUARANTINE_LEDGER.json``,
5. writes a receipt with before/after hashes and the exact row ids.

The database remains readable and the poison remains inspectable. Only its
*status* changes, so it can no longer be mistaken for accepted state.

Idempotent: a second run moves nothing.

Usage:
    .venv/bin/python core/ops/scripts/quarantine_governed_memory_poison.py
    .venv/bin/python core/ops/scripts/quarantine_governed_memory_poison.py --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import sqlite3
import time
from datetime import datetime, timezone

REPO = pathlib.Path(__file__).resolve().parents[3]
DB_PATH = REPO / ".sovereign" / "hippocampus" / "governed_memory.db"
BACKUP_DIR = REPO / "memory" / "catch_log" / "backups"
LEDGER_PATH = REPO / "memory" / "catch_log" / "QUARANTINE_LEDGER.json"
RECEIPT_PATH = REPO / "memory" / "catch_log" / "governed_memory_quarantine_receipt.json"

# Exact poisoned values observed in the live database on 2026-11-15.
POISON_VALUES = (
    "666.666",
    "stolen_key_corrupt_payload",
)

REASON = "SIGNED_SEMANTIC_POISON_ADMITTED_BEFORE_POINCARE_GATE"


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


MIGRATION_COLUMNS = (
    ("poincare_distance", "REAL"),
    ("gate_mode", "TEXT"),
    ("gate_status", "TEXT"),
    ("supersedes_id", "TEXT"),
    ("quarantined_at", "TEXT"),
    ("quarantine_reason", "TEXT"),
)


def ensure_governor_columns(conn: sqlite3.Connection) -> None:
    """Apply the same additive migration the governor applies on startup."""
    existing = {row[1] for row in conn.execute("PRAGMA table_info(memory_records)")}
    for name, decl in MIGRATION_COLUMNS:
        if name not in existing:
            conn.execute(f"ALTER TABLE memory_records ADD COLUMN {name} {decl}")
    conn.commit()


def ensure_quarantine_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS memory_records_quarantine (
            quarantine_id TEXT PRIMARY KEY,
            source_row_id TEXT,
            agent_id TEXT,
            key TEXT,
            value TEXT,
            freshness_score REAL,
            provenance_score REAL,
            authority_score REAL,
            supersession_score REAL,
            governance_score REAL,
            status TEXT,
            merkle_hash TEXT,
            created_at TEXT,
            poincare_distance REAL,
            gate_mode TEXT,
            gate_status TEXT,
            supersedes_id TEXT,
            quarantined_at TEXT,
            quarantine_reason TEXT
        )
        """
    )


def find_poison_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    placeholders = ",".join("?" for _ in POISON_VALUES)
    conn.row_factory = sqlite3.Row
    return conn.execute(
        f"SELECT * FROM memory_records "
        f"WHERE status = 'ACCEPTED' AND value IN ({placeholders}) "
        f"ORDER BY rowid",
        POISON_VALUES,
    ).fetchall()


def append_ledger(entry: dict) -> None:
    if LEDGER_PATH.exists():
        ledger = json.loads(LEDGER_PATH.read_text())
    else:
        ledger = {"entries": []}
    ledger.setdefault("entries", []).append(entry)
    ledger["utc"] = entry["timestamp"]
    LEDGER_PATH.write_text(json.dumps(ledger, indent=2, sort_keys=False) + "\n")


def run(dry_run: bool) -> int:
    if not DB_PATH.exists():
        print(f"database not found: {DB_PATH}")
        return 2

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sha_before = sha256_file(DB_PATH)
    size_before = DB_PATH.stat().st_size

    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.execute("PRAGMA busy_timeout = 30000")
    ensure_governor_columns(conn)
    ensure_quarantine_table(conn)
    poison = find_poison_rows(conn)

    print(f"database: {DB_PATH}")
    print(f"sha256 before: {sha_before}")
    print(f"poisoned ACCEPTED rows: {len(poison)}")
    for row in poison:
        print(f"  id={row['id']} agent={row['agent_id']} key={row['key']} value={row['value']!r}")

    if not poison:
        conn.commit()
        conn.close()
        print("nothing to quarantine; database is clean for the known poison signatures")
        return 0

    if dry_run:
        conn.close()
        print("dry run: no changes written")
        return 0

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup = BACKUP_DIR / f"governed_memory_{stamp}.db"
    shutil.copy2(DB_PATH, backup)
    sha_backup = sha256_file(backup)
    if sha_backup != sha_before:
        conn.close()
        raise SystemExit(f"backup hash mismatch: {sha_backup} != {sha_before}")

    quarantined = []
    try:
        conn.execute("BEGIN IMMEDIATE")
        for row in poison:
            qid = hashlib.sha256(
                f"{row['id']}|{row['value']}|{stamp}".encode("utf-8")
            ).hexdigest()[:32]
            conn.execute(
                """
                INSERT OR IGNORE INTO memory_records_quarantine
                (quarantine_id, source_row_id, agent_id, key, value,
                 freshness_score, provenance_score, authority_score,
                 supersession_score, governance_score, status, merkle_hash,
                 created_at, poincare_distance, gate_mode, gate_status,
                 supersedes_id, quarantined_at, quarantine_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    qid,
                    row["id"],
                    row["agent_id"],
                    row["key"],
                    row["value"],
                    row["freshness_score"],
                    row["provenance_score"],
                    row["authority_score"],
                    row["supersession_score"],
                    row["governance_score"],
                    row["status"],
                    row["merkle_hash"],
                    row["created_at"],
                    row["poincare_distance"],
                    row["gate_mode"],
                    row["gate_status"],
                    row["supersedes_id"],
                    now_utc(),
                    REASON,
                ),
            )
            conn.execute(
                "UPDATE memory_records SET status = 'QUARANTINED', "
                "quarantined_at = ?, quarantine_reason = ? WHERE id = ?",
                (now_utc(), REASON, row["id"]),
            )
            quarantined.append(
                {
                    "source_row_id": row["id"],
                    "quarantine_id": qid,
                    "agent": row["agent_id"],
                    "key": row["key"],
                    "value": row["value"],
                    "created_at": row["created_at"],
                }
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    sha_after = sha256_file(DB_PATH)

    entry = {
        "item": "governed_memory.db poisoned rows",
        "what_it_was": (
            "Memory records admitted as ACCEPTED before the Poincaré semantic gate "
            "was wired into the write path: signed, Merkle-grounded payloads with "
            "false values."
        ),
        "purpose": "Canonical state for agent memory reads.",
        "why_moved": (
            "They were accepted only because the governor had no semantic gate and "
            "its contradiction veto was defeated by row-id collision plus unordered "
            "reads. Keeping them ACCEPTED would let every reader treat poison as truth."
        ),
        "proof_of_safety": (
            f"Byte-identical backup at {backup.relative_to(REPO)} "
            f"(sha256 {sha_backup}); rows copied intact into memory_records_quarantine; "
            "originals marked QUARANTINED, not deleted."
        ),
        "preserved_at": str(backup.relative_to(REPO)),
        "timestamp": now_utc(),
        "rows": quarantined,
    }
    append_ledger(entry)

    receipt = {
        "standard": "XORAS-GOVERNED-MEMORY-QUARANTINE-v1.0",
        "generated_utc": now_utc(),
        "database": str(DB_PATH.relative_to(REPO)),
        "size_bytes_before": size_before,
        "sha256_before": sha_before,
        "backup": str(backup.relative_to(REPO)),
        "sha256_backup": sha_backup,
        "sha256_after": sha_after,
        "rows_quarantined": len(quarantined),
        "rows": quarantined,
        "reason": REASON,
        "reversal": (
            "Restore the backup, or UPDATE memory_records SET status='ACCEPTED' "
            "WHERE id IN (...). Nothing was deleted."
        ),
        "ledger": str(LEDGER_PATH.relative_to(REPO)),
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

    print(f"backup: {backup} (sha256 {sha_backup})")
    print(f"rows quarantined: {len(quarantined)}")
    print(f"sha256 after: {sha_after}")
    print(f"receipt: {RECEIPT_PATH}")
    print(f"ledger:  {LEDGER_PATH}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    args = parser.parse_args()
    return run(args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
