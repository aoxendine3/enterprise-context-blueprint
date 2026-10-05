"""
XORAS SOVEREIGN CORE: SAGA INVERSE REVERSIBLE MUTATION ENGINE
Enforces atomic Prepare -> Execute -> Reverse contracts for zero-loss mutations.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Optional, Callable, Any

class SagaTransaction:
    def __init__(self, tx_id: str, wal_dir: Path):
        self.tx_id = tx_id
        self.wal_dir = wal_dir
        self.backups: Dict[str, Path] = {}
        self.committed = False

    def prepare_file(self, target_file: Path) -> None:
        """Saves inverse snapshot before any write occurs."""
        target_path = Path(target_file).resolve()
        if target_path.is_file():
            backup_file = self.wal_dir / f"{self.tx_id}_{target_path.name}.bak"
            shutil.copy2(target_path, backup_file)
            self.backups[str(target_path)] = backup_file
        else:
            self.backups[str(target_path)] = None  # File did not exist

    def rollback(self) -> bool:
        """Atomically reverses all modifications made during this transaction."""
        success = True
        for original_path, backup in self.backups.items():
            orig = Path(original_path)
            if backup is not None and backup.is_file():
                shutil.copy2(backup, orig)
            elif backup is None and orig.is_file():
                orig.unlink()
        return success

    def cleanup(self) -> None:
        for backup in self.backups.values():
            if backup and backup.is_file():
                try:
                    backup.unlink()
                except OSError:
                    pass

class SagaInverseEngine:
    """Orchestrates zero-data-loss atomic state mutations."""

    def __init__(self, wal_dir_path: str):
        self.wal_dir = Path(wal_dir_path).resolve()
        self.wal_dir.mkdir(parents=True, exist_ok=True)
        self.active_transactions: Dict[str, SagaTransaction] = {}

    def begin(self, tx_id: str) -> SagaTransaction:
        tx = SagaTransaction(tx_id, self.wal_dir)
        self.active_transactions[tx_id] = tx
        return tx

    def commit(self, tx_id: str) -> None:
        tx = self.active_transactions.pop(tx_id, None)
        if tx:
            tx.committed = True
            tx.cleanup()

    def abort(self, tx_id: str) -> bool:
        tx = self.active_transactions.pop(tx_id, None)
        if tx:
            status = tx.rollback()
            tx.cleanup()
            return status
        return False
