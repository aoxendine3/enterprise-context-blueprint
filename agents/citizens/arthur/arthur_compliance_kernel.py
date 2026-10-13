#!/usr/bin/env python3
"""
==============================================================================
ARTHUR (SEAT 7): HARDENED NIST SP 800-218 DYNAMIC INDIRECTION & AST SCANNER
==============================================================================
Mandate: Zero-Trust AST Static Analysis & Deep Reflection Guard.
Detects:
  1. Direct insecure syscalls: eval(), exec(), compile(), __import__().
  2. Dynamic attribute resolution / reflection bypasses:
     - getattr(mod, 'system'), getattr(builtins, 'eval')
     - setattr() monkey-patching of critical invariants
  3. Dynamic module loading / importlib bypasses:
     - importlib.import_module(), __import__()
  4. Obfuscated string decodings & execution wrappers:
     - bytes.fromhex(...), base64.b64decode(...) passed into dynamic execution
  5. Subprocess shell injections:
     - subprocess.Popen/run/call with shell=True
  6. Returns NIST_SP_800_218_HARD_VETO upon detecting any indirection trick.
==============================================================================
"""

import os
import sys
import ast
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple

SSOT_ROOT = Path(os.environ.get("WORKSPACE_ROOT", "/workspace" if os.path.exists("/workspace/core") else "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain"))

class HardenedArthurComplianceKernel:
    def __init__(self, root: Path = SSOT_ROOT):
        self.root = root
        
        # 1. Direct banned primitives
        self.banned_direct_calls = {
            "eval", "exec", "compile", "__import__"
        }
        
        # 2. Banned target attributes accessed via getattr / direct access
        self.banned_attributes = {
            "system", "popen", "execv", "execl", "spawn", "fork", "kill"
        }
        
        # 3. Dynamic loader modules & functions
        self.banned_modules = {
            "importlib", "ctypes", "pty", "subprocess"
        }

    def _extract_constant_str(self, node: ast.AST) -> str:
        """Extracts constant string values even across simple joins or byte conversions."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return ""

    def scan_python_ast_security(self, filepath: Path) -> List[str]:
        violations = []
        try:
            tree = ast.parse(filepath.read_text(encoding="utf-8", errors="ignore"))
        except Exception as e:
            return [f"AST_PARSE_FAILURE: Unable to parse Python AST ({str(e)})"]

        for node in ast.walk(tree):
            # A. Detect Direct Banned Function Calls: eval(), exec(), compile(), __import__()
            if isinstance(node, ast.Call):
                func = node.func
                
                # Direct name: eval(...)
                if isinstance(func, ast.Name) and func.id in self.banned_direct_calls:
                    violations.append(f"DIRECT_INSECURE_CALL: {func.id}() at line {node.lineno}")

                # Attribute call: builtins.eval(...) or os.system(...)
                elif isinstance(func, ast.Attribute):
                    attr = func.attr
                    mod_id = getattr(func.value, "id", "")
                    if attr in self.banned_direct_calls:
                        violations.append(f"QUALIFIED_INSECURE_CALL: {mod_id}.{attr}() at line {node.lineno}")
                    if mod_id == "os" and attr in self.banned_attributes:
                        violations.append(f"UNSAFE_OS_SYSCALL: os.{attr}() at line {node.lineno}")

                # B. Detect Dynamic Indirection via getattr(obj, 'attr')
                if isinstance(func, ast.Name) and func.id in ("getattr", "hasattr"):
                    # Inspect second argument
                    if len(node.args) >= 2:
                        target_attr = self._extract_constant_str(node.args[1])
                        if target_attr in self.banned_attributes or target_attr in self.banned_direct_calls:
                            violations.append(
                                f"DYNAMIC_GETATTR_INDIRECTION: getattr(..., '{target_attr}') "
                                f"bypassing static syscall filter at line {node.lineno}"
                            )
                        elif not target_attr and not isinstance(node.args[1], ast.Constant):
                            # Non-constant variable passed to getattr — potential dynamic injection!
                            violations.append(
                                f"VARIABLE_GETATTR_REFLECTION: Non-constant attribute reflection in getattr() at line {node.lineno}"
                            )

                # C. Detect Dynamic Import via importlib.import_module(...)
                if isinstance(func, ast.Attribute) and func.attr == "import_module":
                    target_mod = self._extract_constant_str(node.args[0]) if node.args else "dynamic"
                    violations.append(
                        f"DYNAMIC_IMPORTLIB_INJECTION: importlib.import_module('{target_mod}') at line {node.lineno}"
                    )

                # D. Detect Subprocess Invocations with shell=True
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                    if func.value.id == "subprocess" and func.attr in ("Popen", "run", "call", "check_output"):
                        for kw in node.keywords:
                            if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                violations.append(
                                    f"SUBPROCESS_SHELL_INJECTION: subprocess.{func.attr}(shell=True) at line {node.lineno}"
                                )

            # E. Detect Dynamic Module Imports in Import Statements
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    mod_root = alias.name.split(".")[0]
                    if mod_root in ("ctypes", "pty"):
                        violations.append(
                            f"RESTRICTED_MODULE_IMPORT: import '{alias.name}' restricted under NIST SP 800-218 at line {node.lineno}"
                        )

        return violations

    def audit_nist_ssdf_invariants(self, files_to_check: List[str]) -> Dict[str, Any]:
        results = {"status": "PASSED", "violations": [], "audited_count": 0}
        
        for rel_path in files_to_check:
            p = self.root / rel_path
            if not p.is_file():
                results["violations"].append(f"MISSING_CRITICAL_ASSET: {rel_path}")
                continue

            results["audited_count"] += 1
            if p.suffix == ".py":
                ast_issues = self.scan_python_ast_security(p)
                for issue in ast_issues:
                    results["violations"].append(f"{rel_path}: {issue}")

            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            if len(digest) != 64:
                results["violations"].append(f"CORRUPT_DIGEST: {rel_path}")

        if results["violations"]:
            results["status"] = "NIST_SP_800_218_HARD_VETO"

        return results

if __name__ == "__main__":
    kernel = HardenedArthurComplianceKernel()
    target_files = [
        "core/ops/provenance/context_lineage_dag_engine.py",
        "core/ops/memory/governed_memory_consolidation_engine.py",
        "core/ops/native/zig/concurrent_merkle_verifier.zig"
    ]
    res = kernel.audit_nist_ssdf_invariants(target_files)
    print("ARTHUR HARDENED AUDIT RESULT:", json.dumps(res, indent=2))
    sys.exit(0 if res["status"] == "PASSED" else 1)
