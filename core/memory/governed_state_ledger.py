"""
State Isolation & Governed CAS Write Ledger
==========================================
Enforces:
1. Judge-Gate: Single-Writer Principle. Every key has exactly one designated Owner Agent.
   Non-owner agents cannot commit direct writes; they must propose mutations.
2. Witness-Gate: Optimistic Concurrency Control (CAS). Writes require matching expected_version.
   Monotonically incrementing versions reject stale writes.
3. Write Ledger: Append-only immutable log recording:
   [timestamp, key, writer, status, expected_version, resulting_version, error_detail]
"""

import os
import json
import time
import threading
from typing import Dict, Any, Optional, Tuple

LEDGER_PATH = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/agent_logs/governed_state_ledger.jsonl"

class StateIsolationEngine:
    def __init__(self, ledger_file: str = LEDGER_PATH):
        self.ledger_file = ledger_file
        os.makedirs(os.path.dirname(self.ledger_file), exist_ok=True)
        self._lock = threading.Lock()
        # In-memory authoritative store: key -> { 'value': any, 'version': int, 'owner': str, 'updated_at': float }
        self._store: Dict[str, Dict[str, Any]] = {}

    def register_key(self, key: str, owner: str, initial_value: Any = None) -> None:
        """Register a key with a strict owner agent."""
        with self._lock:
            if key not in self._store:
                self._store[key] = {
                    "value": initial_value,
                    "version": 1,
                    "owner": owner.lower(),
                    "updated_at": time.time()
                }
                self._log_entry(key, owner, "REGISTER", 0, 1, "Key registered successfully")

    def get(self, key: str) -> Optional[Tuple[Any, int, str]]:
        """Get current value, version, and owner for a key."""
        with self._lock:
            cell = self._store.get(key)
            if cell is None:
                return None
            return cell["value"], cell["version"], cell["owner"]

    def write(self, key: str, writer: str, new_value: Any, expected_version: int) -> Tuple[bool, int, str]:
        """
        Judge-Gate & Witness-Gate Commit:
        - Writer MUST match the registered owner (Judge-Gate).
        - expected_version MUST match current version (Witness-Gate CAS).
        Returns (success: bool, current_or_new_version: int, message: str)
        """
        writer = writer.lower()
        with self._lock:
            if key not in self._store:
                msg = f"Key '{key}' not registered in governed state ledger"
                self._log_entry(key, writer, "REJECT_UNREGISTERED", expected_version, 0, msg)
                return False, 0, msg

            cell = self._store[key]

            # 1. Judge-Gate: Owner Verification
            if cell["owner"] != writer:
                msg = f"JUDGE_GATE_VIOLATION: Writer '{writer}' is not designated owner '{cell['owner']}' for key '{key}'"
                self._log_entry(key, writer, "REJECT_UNAUTHORIZED", expected_version, cell["version"], msg)
                return False, cell["version"], msg

            # 2. Witness-Gate: Version Verification (CAS)
            if cell["version"] != expected_version:
                msg = f"WITNESS_GATE_VIOLATION: Stale write. Expected version {expected_version}, but current version is {cell['version']}"
                self._log_entry(key, writer, "REJECT_STALE_VERSION", expected_version, cell["version"], msg)
                return False, cell["version"], msg

            # Commit Update
            new_version = cell["version"] + 1
            cell["value"] = new_value
            cell["version"] = new_version
            cell["updated_at"] = time.time()

            msg = f"COMMIT_SUCCESS: Version updated {expected_version} -> {new_version}"
            self._log_entry(key, writer, "COMMIT", expected_version, new_version, msg)
            return True, new_version, msg

    def _log_entry(self, key: str, writer: str, status: str, expected_ver: int, resulting_ver: int, details: str):
        entry = {
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "key": key,
            "writer": writer,
            "status": status,
            "expected_version": expected_ver,
            "resulting_version": resulting_ver,
            "details": details
        }
        with open(self.ledger_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
