"""
XMARS Hyper-Accelerated Synthetic Training Engine (X-HASTE)
Module: repo_ingestion_miner.py
Extracts ASTs, functions, invariants, and architecture schemas
from all institutional and sovereign repositories.
"""

import os
import sys
import json
import time
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Any

SSOT_ROOT = "C:/Users/admin/Desktop/SSOT_Agentic_Brain"
INST_ROOT = "C:/Users/admin/Downloads/xoras-core-institutional-release/xoras-core"
OUTPUT_DIR = Path("C:/Users/admin/Desktop/SSOT_Agentic_Brain/data_center/synthetic_training")

IGNORE_DIRS = {
    ".git", "node_modules", "bin", "__pycache__", "venv", ".venv",
    "target", "dist", "archives", "history", "sandbox_stress", ".next", ".cache"
}
VALID_EXTS = {".py", ".rs", ".cs", ".cpp", ".h", ".js", ".ts", ".json", ".md", ".yaml", ".yml", ".toml"}

class RepoIngestionMiner:
    def __init__(self):
        self.catalog = []
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def scan_repo(self, root_str: str, repo_tag: str) -> List[Dict[str, Any]]:
        extracted = []
        if not os.path.exists(root_str):
            print(f"[MINER] Root {root_str} does not exist, skipping.")
            return extracted

        print(f"[MINER] Commencing high-density mining of repo [{repo_tag}]: {root_str}")
        for root, dirs, files in os.walk(root_str, topdown=True, onerror=lambda e: None):
            # In-place filter to avoid traversing ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]

            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in VALID_EXTS:
                    continue

                full_path = os.path.join(root, filename)
                try:
                    rel_path = os.path.relpath(full_path, root_str)
                except Exception:
                    rel_path = filename

                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                except Exception:
                    continue

                if not content.strip() or len(content) > 500000:
                    continue

                sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
                units = self.extract_code_units(content, ext)

                entry = {
                    "repo": repo_tag,
                    "relative_path": rel_path,
                    "extension": ext,
                    "size_bytes": len(content),
                    "sha256": sha[:16],
                    "units_count": len(units),
                    "units": units,
                    "summary": content[:400].replace("\n", " ").strip()
                }
                extracted.append(entry)

        print(f"[MINER] [{repo_tag}] Ingested {len(extracted)} source files.")
        return extracted

    def extract_code_units(self, content: str, ext: str) -> List[Dict[str, Any]]:
        units = []
        if ext == ".py":
            for m in re.finditer(r"^(?:async\s+)?def\s+([a-zA-Z0-9_]+)\s*\((.*?)\):", content, re.MULTILINE):
                units.append({"type": "function", "name": m.group(1), "args": m.group(2).strip()})
            for m in re.finditer(r"^class\s+([a-zA-Z0-9_]+)(?:\((.*?)\))?:", content, re.MULTILINE):
                units.append({"type": "class", "name": m.group(1), "bases": m.group(2) or ""})
        elif ext in {".js", ".ts"}:
            for m in re.finditer(r"(?:function|class|const|let)\s+([a-zA-Z0-9_]+)\s*=?\s*(?:function|\(.*?\)\s*=>|\{)", content):
                units.append({"type": "declaration", "name": m.group(1)})
        elif ext in {".rs", ".cs", ".cpp", ".h"}:
            for m in re.finditer(r"(?:fn|class|struct|interface|void|int|bool)\s+([a-zA-Z0-9_]+)\s*[\(\{]", content):
                units.append({"type": "native_symbol", "name": m.group(1)})
        elif ext == ".md":
            for m in re.finditer(r"^(#{1,3})\s+(.+)$", content, re.MULTILINE):
                units.append({"type": "heading", "name": m.group(2).strip()})
        return units[:20]

    def run(self) -> Dict[str, Any]:
        t0 = time.perf_counter()
        ssot_files = self.scan_repo(SSOT_ROOT, "SSOT_Agentic_Brain")
        inst_files = self.scan_repo(INST_ROOT, "xoras_core_institutional")

        total_files = len(ssot_files) + len(inst_files)
        total_units = sum(f["units_count"] for f in ssot_files) + sum(f["units_count"] for f in inst_files)
        elapsed = round(time.perf_counter() - t0, 3)

        catalog_data = {
            "version": "1.0.0-HASTE",
            "timestamp": time.time(),
            "mining_duration_sec": elapsed,
            "total_files": total_files,
            "total_code_units": total_units,
            "repos": {
                "SSOT_Agentic_Brain": len(ssot_files),
                "xoras_core_institutional": len(inst_files)
            },
            "files": ssot_files + inst_files
        }

        out_file = OUTPUT_DIR / "mined_code_catalog.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(catalog_data, f, indent=2)

        print(f"[MINER] Complete. Mined {total_files} files ({total_units} units) in {elapsed}s.")
        print(f"[MINER] Saved catalog to: {out_file}")
        return catalog_data

if __name__ == "__main__":
    miner = RepoIngestionMiner()
    miner.run()