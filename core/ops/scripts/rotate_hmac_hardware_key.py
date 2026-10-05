#!/usr/bin/env python3
"""
Hardware HMAC Key Rotation Engine
---------------------------------
Generates a new cryptographically secure 256-bit secret, saves it to
.sovereign/crypto_keys/hmac_hardware_key.bin with 0600 permissions,
and re-calculates HMAC signatures across all 3,164 nodes in lineage_dag.db.
"""

import os
import sys
import secrets
import sqlite3
import hashlib
import hmac
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
KEY_FILE = ROOT / ".sovereign" / "crypto_keys" / "hmac_hardware_key.bin"
DB_PATH = ROOT / ".sovereign" / "provenance" / "lineage_dag.db"

def rotate_key():
    print("==========================================================================")
    print("  HARDWARE HMAC KEY ROTATION & RE-SIGNING ENGINE")
    print("==========================================================================")

    # 1. Generate new 256-bit secret key
    new_key = secrets.token_bytes(32)
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    KEY_FILE.write_bytes(new_key)
    os.chmod(KEY_FILE, 0o600)
    print(f"✅ Generated new 256-bit secure HMAC key at {KEY_FILE}")

    # 2. Re-sign all lineage DAG nodes with rotated key
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT rowid, node_id, payload_hash FROM lineage_nodes;")
    rows = cur.fetchall()

    re_signed = 0
    for r in rows:
        msg = f"{r['node_id']}:{r['payload_hash']}".encode('utf-8')
        new_sig = hmac.new(new_key, msg, hashlib.sha256).hexdigest()
        cur.execute("UPDATE lineage_nodes SET signature = ? WHERE rowid = ?", (new_sig, r['rowid']))
        re_signed += 1

    conn.commit()
    conn.close()

    print(f"✅ Re-signed {re_signed} nodes in lineage_dag.db with rotated HMAC key.")
    print("==========================================================================")

if __name__ == "__main__":
    rotate_key()
