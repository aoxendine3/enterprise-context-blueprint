# --- XORAS SYSTEMS: MEMORY SENTINEL DAEMON ---
# File: Source/xoras_memory_sentinel.py
# Classification: [PRODUCTION // SOVEREIGN DAEMON]

import os
import sys
import time
import sqlite3
import datetime
import json
from typing import Dict, Any, List

# Strict Paths
WORKSPACE_ROOT = "/Users/ajoxendine68/Desktop/Xoras_Workspace"
MEMORY_DB_PATH = os.path.expanduser("~/.sovereign/hippocampus/xoras_memory.db")
LOG_PATH = os.path.join(WORKSPACE_ROOT, "AI_Core/Xoras_Project/xoras-core/Omni_Dojo_Sandbox/xoras_memory_sentinel.log")

MONITORED_PATHS = {
    "xoras-startup": os.path.join(WORKSPACE_ROOT, "AI_Core/Xoras/AI_Core/Xoras_Agent_Skills/xoras-startup"),
    "xoras-core": os.path.join(WORKSPACE_ROOT, "AI_Core/Xoras_Project/xoras-core"),
    "xoras-app": os.path.join(WORKSPACE_ROOT, "AI_Core/Xoras_Project/xoras-app"),
    "xoras-config": os.path.join(WORKSPACE_ROOT, "AI_Core/Xoras_Project/xoras-config"),
    "prompt-guard": os.path.join(WORKSPACE_ROOT, "AI_Core/Xoras_Knowledge/innovations/01_prompt_guard_monitor.py"),
    "dojo-archivist": os.path.join(WORKSPACE_ROOT, "AI_Core/Xoras_Project/xoras-core/Source/dojo_archivist.py")
}

def log_event(msg: str) -> None:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")

def init_db():
    db_dir = os.path.dirname(MEMORY_DB_PATH)
    os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(MEMORY_DB_PATH)
    try:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS file_registry (
            key TEXT PRIMARY KEY,
            resolved_path TEXT NOT NULL,
            exists_status INTEGER NOT NULL,
            last_checked TEXT NOT NULL
        )
        """)
        conn.commit()
    finally:
        conn.close()

def sync_memory_registry():
    conn = sqlite3.connect(MEMORY_DB_PATH)
    try:
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        log_event("[SENTINEL] Commencing periodic workspace path integrity audit...")
        
        for key, path in MONITORED_PATHS.items():
            exists = 1 if os.path.exists(path) else 0
            status_text = "FOUND" if exists else "MISSING"
            
            conn.execute("""
            INSERT OR REPLACE INTO file_registry (key, resolved_path, exists_status, last_checked)
            VALUES (?, ?, ?, ?)
            """, (key, path, exists, ts))
            
            log_event(f"[SENTINEL] Path verification: {key} -> {status_text} at {path}")
            
        conn.commit()
        log_event("[SENTINEL] Workspace integrity audit complete. Memory state consolidated.")
    except Exception as e:
        log_event(f"[SENTINEL] Error during registry sync: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    log_event("Xoras Memory Sentinel Daemon started.")
    # Run once synchronously
    sync_memory_registry()
