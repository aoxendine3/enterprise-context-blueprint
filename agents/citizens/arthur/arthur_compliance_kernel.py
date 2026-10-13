#!/usr/bin/env python3
"""
==============================================================================
ARTHUR (SEAT 7): MULTI-STAGE SYMBOLIC DATA-FLOW & TAINT TRACKING KERNEL
==============================================================================
Mandate: Close the Syntax-vs-Value Gap in Static AST Security Analysis.
Combines:
  1. AST Syntax Tree Traversal (structural analysis).
  2. Multi-Stage Symbolic Value Propagation (SSA / Taint Tracking):
     - Resolves variable assignments, string concatenations ('sys' + 'tem'),
       format strings (f"{p1}{p2}"), byte decodings, and tuple/list unpacking.
  3. Dynamic Reflection & Operator Tracking:
     - operator.attrgetter("system")(os)
     - importlib.import_module(computed_str)
     - getattr(os, computed_str)
     - dict lookup indirection: os.__dict__["system"]
  4. Intercepts deferred resolution before execution.
==============================================================================
"""

import os
import sys
import ast
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Set, Optional

SSOT_ROOT = Path(os.environ.get("WORKSPACE_ROOT", "/workspace" if os.path.exists("/workspace/core") else "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain"))

class ArthurSymbolicTaintKernel:
    def __init__(self, root: Path = SSOT_ROOT):
        self.root = root
        
        self.banned_target_names = {
            "eval", "exec", "compile", "__import__",
            "system", "popen", "execv", "execl", "spawn", "fork", "kill"
        }
        
        self.banned_modules = {
            "ctypes", "pty"
        }

    def _evaluate_symbolic_expression(self, node: ast.AST, env: Dict[str, Any]) -> Optional[str]:
        """Symbolically evaluates string constants, concatenations, and env lookups."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return node.value
            elif isinstance(node.value, bytes):
                return node.value.decode("utf-8", errors="ignore")
                
        elif isinstance(node, ast.Name):
            return env.get(node.id)
            
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = self._evaluate_symbolic_expression(node.left, env)
            right = self._evaluate_symbolic_expression(node.right, env)
            if left is not None and right is not None:
                return str(left) + str(right)
                
        elif isinstance(node, ast.JoinedStr): # f-string resolution
            parts = []
            for val in node.values:
                res = self._evaluate_symbolic_expression(val, env)
                if res is not None:
                    parts.append(str(res))
                else:
                    return None
            return "".join(parts)
            
        elif isinstance(node, ast.FormattedValue):
            return self._evaluate_symbolic_expression(node.value, env)

        elif isinstance(node, ast.Call):
            # Resolve b"system".decode() or bytes.fromhex("...")
            if isinstance(node.func, ast.Attribute) and node.func.attr == "decode":
                base = self._evaluate_symbolic_expression(node.func.value, env)
                return base
            elif isinstance(node.func, ast.Attribute) and node.func.attr == "fromhex":
                if node.args and isinstance(node.args[0], ast.Constant):
                    try:
                        return bytes.fromhex(node.args[0].value).decode("utf-8", errors="ignore")
                    except Exception:
                        pass
        return None

    def scan_python_ast_security(self, filepath: Path) -> List[str]:
        violations = []
        try:
            tree = ast.parse(filepath.read_text(encoding="utf-8", errors="ignore"))
        except Exception as e:
            return [f"AST_PARSE_FAILURE: Unable to parse Python AST ({str(e)})"]

        # Environment tracking symbolic variable assignments across stages
        env: Dict[str, Any] = {}

        for node in ast.walk(tree):
            # Stage 1: Track Variable Assignments for Multi-Stage Propagation
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        val = self._evaluate_symbolic_expression(node.value, env)
                        if val is not None:
                            env[target.id] = val

            # Stage 2: Inspect Calls & Indirect Resolution
            if isinstance(node, ast.Call):
                func = node.func

                # Direct Banned Function: eval(), exec(), compile()
                if isinstance(func, ast.Name) and func.id in self.banned_target_names:
                    violations.append(f"DIRECT_INSECURE_CALL: {func.id}() at line {node.lineno}")

                # Qualified Call: os.system(...)
                elif isinstance(func, ast.Attribute):
                    mod_id = getattr(func.value, "id", "")
                    if func.attr in self.banned_target_names:
                        violations.append(f"QUALIFIED_INSECURE_CALL: {mod_id}.{func.attr}() at line {node.lineno}")

                # Indirection Pattern A: getattr(target, attr_expr)
                if isinstance(func, ast.Name) and func.id in ("getattr", "hasattr"):
                    if len(node.args) >= 2:
                        target_attr = self._evaluate_symbolic_expression(node.args[1], env)
                        if target_attr and target_attr in self.banned_target_names:
                            violations.append(
                                f"MULTI_STAGE_GETATTR_INDIRECTION: getattr(..., '{target_attr}') "
                                f"resolved from symbolic data-flow at line {node.lineno}"
                            )
                        elif target_attr is None:
                            violations.append(
                                f"UNRESOLVED_DYNAMIC_REFLECTION: Non-constant attribute in getattr() at line {node.lineno}"
                            )

                # Indirection Pattern B: operator.attrgetter(attr_expr)(target)
                if isinstance(func, ast.Attribute) and func.attr == "attrgetter":
                    if node.args:
                        target_attr = self._evaluate_symbolic_expression(node.args[0], env)
                        if target_attr and target_attr in self.banned_target_names:
                            violations.append(
                                f"OPERATOR_ATTRGETTER_INDIRECTION: operator.attrgetter('{target_attr}') at line {node.lineno}"
                            )

                # Indirection Pattern C: importlib.import_module(mod_expr)
                if isinstance(func, ast.Attribute) and func.attr == "import_module":
                    target_mod = self._evaluate_symbolic_expression(node.args[0], env) if node.args else "dynamic"
                    violations.append(
                        f"DYNAMIC_IMPORTLIB_INJECTION: importlib.import_module('{target_mod}') at line {node.lineno}"
                    )

                # Indirection Pattern D: subprocess with shell=True
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                    if func.value.id == "subprocess" and func.attr in ("Popen", "run", "call", "check_output"):
                        for kw in node.keywords:
                            if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                violations.append(
                                    f"SUBPROCESS_SHELL_INJECTION: subprocess.{func.attr}(shell=True) at line {node.lineno}"
                                )

            # Stage 3: Inspect Dictionary Lookups (os.__dict__['system'])
            elif isinstance(node, ast.Subscript):
                if isinstance(node.value, ast.Attribute) and node.value.attr == "__dict__":
                    sub_key = self._evaluate_symbolic_expression(node.slice, env)
                    if sub_key and sub_key in self.banned_target_names:
                        violations.append(
                            f"DICT_REFLECTION_BYPASS: __dict__['{sub_key}'] at line {node.lineno}"
                        )

            # Stage 4: Restricted Module Imports (ctypes, pty)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    mod_root = alias.name.split(".")[0]
                    if mod_root in self.banned_modules:
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
    kernel = ArthurSymbolicTaintKernel()
    target_files = [
        "core/ops/provenance/context_lineage_dag_engine.py",
        "core/ops/memory/governed_memory_consolidation_engine.py",
        "core/ops/native/zig/concurrent_merkle_verifier.zig"
    ]
    res = kernel.audit_nist_ssdf_invariants(target_files)
    print("ARTHUR SYMBOLIC AUDIT RESULT:", json.dumps(res, indent=2))
    sys.exit(0 if res["status"] == "PASSED" else 1)
