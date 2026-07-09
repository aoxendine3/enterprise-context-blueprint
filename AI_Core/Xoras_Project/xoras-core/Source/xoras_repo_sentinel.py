# --- XORAS SYSTEMS: GIT AND REPO AUDITOR ---
# File: Source/xoras_repo_sentinel.py
# Classification: [PRODUCTION // SOVEREIGN DAEMON]

import os
import sys
import time
import sqlite3
import datetime
import subprocess

# Strict Paths
WORKSPACE_ROOT = "/Users/ajoxendine68/Desktop/Xoras_Workspace"
CORE_REPO_PATH = os.path.join(WORKSPACE_ROOT, "AI_Core/Xoras_Project/xoras-core")
MEMORY_DB_PATH = os.path.expanduser("~/.sovereign/hippocampus/xoras_memory.db")
LOG_PATH = os.path.join(WORKSPACE_ROOT, "AI_Core/Xoras_Project/xoras-core/Omni_Dojo_Sandbox/xoras_repo_sentinel.log")

def log_event(msg: str) -> None:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")

def init_db():
    conn = sqlite3.connect(MEMORY_DB_PATH)
    try:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS git_registry (
            filepath TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            last_checked TEXT NOT NULL
        )
        """)
        conn.commit()
    finally:
        conn.close()

def audit_git_changes():
    if not os.path.exists(CORE_REPO_PATH):
        log_event(f"[REPO-SENTINEL] Core repository path not found: {CORE_REPO_PATH}")
        return
        
    try:
        # Run git status --porcelain
        cmd = ["git", "status", "--porcelain"]
        res = subprocess.run(cmd, cwd=CORE_REPO_PATH, capture_output=True, text=True, timeout=10)
        
        if res.returncode != 0:
            log_event(f"[REPO-SENTINEL] Git status failed: {res.stderr.strip()}")
            return
            
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conn = sqlite3.connect(MEMORY_DB_PATH)
        
        # Parse lines
        lines = res.stdout.splitlines()
        log_event(f"[REPO-SENTINEL] Scanning {len(lines)} uncommitted file states in repository...")
        
        for line in lines:
            if len(line) < 4:
                continue
            status = line[:2].strip()
            filepath = line[3:].strip()
            
            conn.execute("""
            INSERT OR REPLACE INTO git_registry (filepath, status, last_checked)
            VALUES (?, ?, ?)
            """, (filepath, status, ts))
            
            log_event(f"[REPO-SENTINEL] Synced: {filepath} [Status: {status}]")
            
        conn.commit()
        log_event("[REPO-SENTINEL] Git repository sync complete. Memory updated.")
    except Exception as e:
        log_event(f"[REPO-SENTINEL] Audit error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    audit_git_changes()
