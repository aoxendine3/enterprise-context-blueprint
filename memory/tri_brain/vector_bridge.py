"""
Tri-Brain Vector & HexGraph Bridge:
Connects LanceDB columnar vector storage and HexGraph topological associative nodes
to Container 1, Container 2, and Container 3 of the Tri-Brain.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List

LANCEDB_DIR = Path(__file__).resolve().parent / "lancedb_vault"

class TriBrainVectorStore:
    def __init__(self):
        LANCEDB_DIR.mkdir(parents=True, exist_ok=True)
        self.db = None
        self._init_lancedb()

    def _init_lancedb(self):
        try:
            import lancedb
            self.db = lancedb.connect(str(LANCEDB_DIR))
        except Exception as e:
            self.db = None

    def is_active(self) -> bool:
        return self.db is not None

    def get_info(self) -> Dict[str, Any]:
        return {
            "lancedb_active": self.is_active(),
            "vault_path": str(LANCEDB_DIR),
            "table_count": len(self.db.table_names()) if self.db else 0
        }
