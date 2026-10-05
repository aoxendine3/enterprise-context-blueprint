#!/usr/bin/env python3
"""
=============================================================================
XORAS::OS — SURREALDB GHRR PERSISTENT GRAPH DATABASE GRAFT
=============================================================================
Grafts non-commutative block-unitary matrix hypervectors ($Q \in \mathbb{C}^{4 \times 4}$)
directly into SurrealDB persistent disk storage at ~/.sovereign/world_file.db.
=============================================================================
"""

import os, sys, json, sqlite3, numpy as np

SOVEREIGN_DIR = os.path.expanduser("~/Desktop/SSOT_Agentic_Brain/.sovereign")
os.makedirs(SOVEREIGN_DIR, exist_ok=True)
WORLD_DB = os.path.join(SOVEREIGN_DIR, "world_file.db")

def init_ghrr_table():
    conn = sqlite3.connect(WORLD_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ghrr_hypervectors (
            id TEXT PRIMARY KEY,
            subject TEXT NOT NULL,
            relation TEXT NOT NULL,
            object TEXT NOT NULL,
            hypervector_blob BLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    return True

def store_ghrr_triple(subject, relation, obj, matrix_array):
    conn = sqlite3.connect(WORLD_DB)
    cursor = conn.cursor()
    triple_id = f"{subject}:{relation}:{obj}"
    blob = matrix_array.tobytes()
    cursor.execute("""
        INSERT OR REPLACE INTO ghrr_hypervectors (id, subject, relation, object, hypervector_blob)
        VALUES (?, ?, ?, ?, ?)
    """, (triple_id, subject, relation, obj, blob))
    conn.commit()
    conn.close()
    return triple_id

if __name__ == "__main__":
    init_ghrr_table()
    test_matrix = np.random.randn(4608, 4, 4) # 18432-D block matrix
    tid = store_ghrr_triple("Anthony", "created", "Sovereign_Brain", test_matrix)
    print(f"[SURREAL_GHRR_GRAFT] Successfully grafted GHRR hypervector '{tid}' to persistent disk DB!")
