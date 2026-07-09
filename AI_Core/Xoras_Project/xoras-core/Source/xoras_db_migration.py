import json
import sqlite3
import os
import time


def migrate_db():
    json_path = "xoras_memory.json"
    db_path = "xoras_memory.db"

    print(f"[MIGRATION] Starting migration from {json_path} to {db_path}...")

    if not os.path.exists(json_path):
        print(f"[MIGRATION] {json_path} not found. Creating empty DB.")
        memory_bank = []
    else:
        with open(json_path, "r") as f:
            memory_bank = json.load(f)
        print(f"[MIGRATION] Loaded {len(memory_bank)} records from JSON.")

    # Connect to SQLite and enable WAL mode
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")

    # Create schema
    conn.execute("""
    CREATE TABLE IF NOT EXISTS memory_vectors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL,
        vector JSON NOT NULL,
        timestamp REAL NOT NULL,
        domain TEXT NOT NULL,
        metadata JSON NOT NULL
    )
    """)

    # Insert data
    cursor = conn.cursor()
    cursor.execute("BEGIN TRANSACTION;")
    for idx, memory in enumerate(memory_bank):
        vector_str = json.dumps(memory.get("vector", []))
        metadata_str = json.dumps(memory.get("metadata", {}))
        cursor.execute("""
        INSERT INTO memory_vectors (text, vector, timestamp, domain, metadata)
        VALUES (?, ?, ?, ?, ?)
        """, (
            memory.get("text", ""),
            vector_str,
            memory.get("timestamp", time.time()),
            memory.get("domain", "general"),
            metadata_str
        ))
    cursor.execute("COMMIT;")

    # Verify
    cursor.execute("SELECT COUNT(*) FROM memory_vectors")
    count = cursor.fetchone()[0]
    print(f"[MIGRATION] Successfully inserted {count} records into {db_path}.")

    conn.close()


if __name__ == "__main__":
    migrate_db()
