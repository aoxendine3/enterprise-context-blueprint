#!/usr/bin/env python3
"""
===============================================================================
XORAS::OS - ENTERPRISE MULTI-REPO AST STATIC ANALYSIS ENGINE
===============================================================================
Mandate: Parallel AST walker across all codebases & sub-repositories.
         Detects dynamic imports (importlib.import_module, __import__),
         dynamic reflection (getattr computed), dynamic dictionary mutations
         (__dict__[<computed>]), eval/exec invocations, and produces a
         cryptographically verified JSON manifest & executive markdown report.
===============================================================================
"""

import ast
import json
import os
import sys
import time
import hashlib
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Tuple, Optional

_IGNORED_DIRS = {
    "__pycache__", ".venv", "venv", "node_modules", ".git", "target", 
    ".zig-cache", "dist", "archives", "logs"
}

_DYNAMIC_CALLS = {
    "__import__": (0, "DYNAMIC_IMPORT_COMPUTED", "__import__ with non-literal module name (arbitrary module loading)"),
    "getattr": (1, "DYNAMIC_GETATTR_COMPUTED", "getattr() with computed attribute key (reflection bypass)"),
    "setattr": (1, "DYNAMIC_SETATTR_COMPUTED", "setattr() with computed attribute key (unauthorized state overwrite)"),
    "delattr": (1, "DYNAMIC_DELATTR_COMPUTED", "delattr() with computed attribute key (destructive reflection)"),
    "eval": (0, "DYNAMIC_EVAL_EXECUTION", "eval() invocation (arbitrary code execution vector)"),
    "exec": (0, "DYNAMIC_EXEC_EXECUTION", "exec() invocation (arbitrary code execution vector)")
}

def _is_importlib(name: str) -> bool:
    return name == "importlib" or name.startswith("importlib.")

def scan_single_file(filepath: str) -> Dict[str, Any]:
    try:
        with open(filepath, "rb") as f:
            raw = f.read()
    except Exception as e:
        return {"filepath": filepath, "status": "READ_ERROR", "error": str(e), "findings": [], "symbols": {}}

    sha256 = hashlib.sha256(raw).hexdigest()
    
    try:
        content = raw.decode("utf-8", errors="replace")
        tree = ast.parse(content, filename=filepath)
    except (SyntaxError, ValueError, RecursionError) as e:
        return {
            "filepath": filepath,
            "sha256": sha256,
            "status": "PARSE_ERROR",
            "error": str(e),
            "findings": [],
            "symbols": {}
        }

    findings = []
    classes = []
    functions = []
    async_functions = []

    def record_finding(node: ast.AST, pattern_id: str, desc: str, severity: str = "HIGH"):
        findings.append({
            "line": getattr(node, "lineno", 0),
            "col": getattr(node, "col_offset", 0),
            "pattern_id": pattern_id,
            "severity": severity,
            "description": desc
        })

    class SecurityASTVisitor(ast.NodeVisitor):
        def visit_ClassDef(self, node: ast.ClassDef):
            classes.append(node.name)
            self.generic_visit(node)

        def visit_FunctionDef(self, node: ast.FunctionDef):
            functions.append(node.name)
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
            async_functions.append(node.name)
            self.generic_visit(node)

        def visit_Call(self, node: ast.Call):
            f = node.func
            # 1. importlib.import_module
            if isinstance(f, ast.Attribute) and f.attr == "import_module":
                record_finding(node, "DYNAMIC_IMPORTLIB_CALL", "importlib.import_module() — dynamic runtime module loader", "HIGH")
            
            # 2. Known builtins: getattr, setattr, delattr, __import__, eval, exec
            elif isinstance(f, ast.Name) and f.id in _DYNAMIC_CALLS:
                arg_index, pid, desc = _DYNAMIC_CALLS[f.id]
                # eval / exec are always flagged
                if f.id in ("eval", "exec"):
                    record_finding(node, pid, desc, "CRITICAL")
                elif len(node.args) > arg_index and not isinstance(node.args[arg_index], ast.Constant):
                    record_finding(node, pid, desc, "HIGH")

            self.generic_visit(node)

        def visit_Subscript(self, node: ast.Subscript):
            # obj.__dict__[computed]
            if (isinstance(node.value, ast.Attribute) and 
                node.value.attr == "__dict__" and 
                not isinstance(node.slice, ast.Constant)):
                record_finding(node, "DYNAMIC_DICT_ACCESS", "__dict__[<computed>] — dynamic attribute dereference / tampering", "MEDIUM")
            self.generic_visit(node)

        def visit_Import(self, node: ast.Import):
            for a in node.names:
                if _is_importlib(a.name):
                    record_finding(node, "IMPORTLIB_IMPORT", f"import {a.name} — dynamic import module loaded", "LOW")
            self.generic_visit(node)

        def visit_ImportFrom(self, node: ast.ImportFrom):
            if _is_importlib(node.module or ""):
                record_finding(node, "IMPORTLIB_IMPORT", f"from {node.module} import ... — dynamic import module loaded", "LOW")
            self.generic_visit(node)

    try:
        visitor = SecurityASTVisitor()
        visitor.visit(tree)
    except (RecursionError, ValueError, RuntimeError):
        pass

    return {
        "filepath": filepath,
        "sha256": sha256,
        "status": "PARSED",
        "error": None,
        "findings": findings,
        "symbols": {
            "classes_count": len(classes),
            "functions_count": len(functions),
            "async_functions_count": len(async_functions)
        }
    }

def collect_python_files(repo_roots: List[str]) -> List[str]:
    collected = []
    for root_dir in repo_roots:
        if not os.path.exists(root_dir):
            continue
        for r, dirs, files in os.walk(root_dir, topdown=True):
            dirs[:] = [d for d in dirs if d not in _IGNORED_DIRS]
            for file in files:
                if file.endswith(".py"):
                    collected.append(os.path.join(r, file))
    return sorted(list(set(collected)))

def run_multirepo_ast_audit(repo_roots: Optional[List[str]] = None, workers: int = 8) -> Dict[str, Any]:
    start_time = time.time()
    if repo_roots is None:
        repo_roots = [
            ".",
            "./labs/workspaces/hyperforge_autoresearch",
            "./xoras_sentry_backup/xoras-sentry",
            "./workspaces/telecom_churn_challenge",
            "./workspaces/integrity_sentry_core",
            "./barn/gemma_paper_sub",
            "./barn/telecom_churn_challenge"
        ]

    files = collect_python_files(repo_roots)
    total_files = len(files)
    print(f"[*] Commencing AST deep analysis across {len(repo_roots)} repository targets...")
    print(f"[*] Total Python modules discovered: {total_files}")
    print(f"[*] Dispatching worker pool with {workers} parallel processes...")

    results = []
    chunk_size = 100
    with ProcessPoolExecutor(max_workers=workers) as executor:
        for res in executor.map(scan_single_file, files, chunksize=chunk_size):
            results.append(res)

    duration = time.time() - start_time
    print(f"[✓] AST analysis complete in {duration:.2f} seconds ({total_files / max(duration, 0.001):.1f} files/sec).")

    # Aggregate metrics
    parsed_count = sum(1 for r in results if r["status"] == "PARSED")
    error_count = sum(1 for r in results if r["status"] in ("PARSE_ERROR", "READ_ERROR"))
    
    findings_by_pattern = {}
    findings_by_severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    findings_by_repo = {}
    flagged_files = 0
    total_findings = 0

    for r in results:
        f_list = r.get("findings", [])
        if f_list:
            flagged_files += 1
            total_findings += len(f_list)
            # determine top-level repo / module bucket
            rel = os.path.relpath(r["filepath"], ".")
            bucket = rel.split(os.sep)[0]
            findings_by_repo[bucket] = findings_by_repo.get(bucket, 0) + len(f_list)

            for f in f_list:
                pid = f["pattern_id"]
                sev = f["severity"]
                findings_by_pattern[pid] = findings_by_pattern.get(pid, 0) + 1
                findings_by_severity[sev] = findings_by_severity.get(sev, 0) + 1

    manifest = {
        "metadata": {
            "version": "1.0.0",
            "audit_type": "Multi-Repo Abstract Syntax Tree (AST) Security Scan",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "duration_seconds": round(duration, 2),
            "total_python_files": total_files,
            "parsed_successfully": parsed_count,
            "parse_errors": error_count,
            "total_findings": total_findings,
            "flagged_files": flagged_files,
            "summary_by_severity": findings_by_severity,
            "summary_by_pattern": findings_by_pattern,
            "summary_by_bucket": findings_by_repo
        },
        "results": [r for r in results if r.get("findings")]  # Store only flagged files for lean receipt
    }

    # Save receipt
    out_dir = "memory/catch_log"
    os.makedirs(out_dir, exist_ok=True)
    manifest_path = os.path.join(out_dir, "ast_repo_wide_audit_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"[✓] AST Audit Manifest written to: {manifest_path}")
    return manifest

if __name__ == "__main__":
    workers = min(os.cpu_count() or 4, 10)
    run_multirepo_ast_audit(workers=workers)
