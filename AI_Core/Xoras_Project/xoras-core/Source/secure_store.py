import os
import sqlite3
import threading
from typing import Any, Dict, Optional


class SecureMemory:
    """Fast, thread-safe short-term secure in-memory storage."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: Dict[str, Any] = {}

    def save(self, key: str, value: Any) -> None:
        with self._lock:
            self._store[key] = value

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            return self._store.get(key)


class LongTermArchive:
    """Persistent, SQLite-backed long-term secure database storage."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(current_dir, "xoras_memory.db")
        self.db_path = db_path
        self._lock = threading.Lock()
        self._initialize_db()

    def _initialize_db(self) -> None:
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS long_term_archive (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        timestamp REAL DEFAULT (strftime('%s', 'now'))
                    )
                    """
                )
                conn.commit()
            finally:
                conn.close()

    def save(self, key: str, value: Any) -> None:
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute(
                    "INSERT OR REPLACE INTO long_term_archive (key, value) VALUES (?, ?)",
                    (key, str(value)),
                )
                conn.commit()
            finally:
                conn.close()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT value FROM long_term_archive WHERE key = ?", (key,)
                )
                row = cursor.fetchone()
                return row[0] if row else None
            finally:
                conn.close()
