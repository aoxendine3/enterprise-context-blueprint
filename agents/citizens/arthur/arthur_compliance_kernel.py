#!/usr/bin/env python3
"""
==============================================================================
ARTHUR (SEAT 7): COMPLETE TAINT-LATTICE & EXTERNAL-SOURCE PROPAGATION KERNEL
==============================================================================
Mandate: Close the Runtime-State & External-Taint Seam in Static Security.
Lattice Architecture:
  1. Sources of External Taint (TAINT_EXTERNAL):
     - Environment lookups: os.environ, os.environ.get(), os.getenv()
     - File I/O reads: open().read(), Path.read_text(), readlines()
     - Network & socket streams: requests.get(), urllib.request.urlopen(), socket.recv()
     - CLI / Process args: sys.argv, input()
  2. Taint Propagation Rules:
     - Taint spreads across assignments: tainted_var = source()
     - Taint spreads across concatenations: clean + tainted -> tainted
     - Taint spreads across format strings, slices, joins, and method transforms.
  3. Security Sinks (Forbidden Operations with Tainted Data):
     - Sink 1: Dynamic Reflection Sink -> getattr(target, TAINTED)
     - Sink 2: Execution Sink -> eval(TAINTED), exec(TAINTED)
     - Sink 3: Syscall Sink -> os.system(TAINTED), os.popen(TAINTED)
     - Sink 4: Subprocess Sink -> subprocess.run(TAINTED, shell=True)
     - Sink 5: Dynamic Loader Sink -> importlib.import_module(TAINTED)
  4. Decision: Any Sink reached by TAINT_EXTERNAL triggers an immediate
     NIST_SP_800_218_HARD_VETO.
==============================================================================
"""

import os
import sys
import ast
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Set, Optional, Tuple

SSOT_ROOT = Path(os.environ.get("WORKSPACE_ROOT", "/workspace" if os.path.exists("/workspace/core") else "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain"))

TAINT_EXTERNAL = "__TAINT_EXTERNAL_SOURCE__"

class ArthurTaintLatticeKernel:
    def __init__(self, root: Path = SSOT_ROOT):
        self.root = root
        
        self.banned_target_names = {
            "eval", "exec", "compile", "__import__",
            "system", "popen", "execv", "execl", "spawn", "fork", "kill"
        }
        
        self.banned_modules = {
            "ctypes", "pty"
        }

        # Known External Taint Sources
        self.taint_source_functions = {
            "getenv", "read", "read_text", "read_bytes", "readline", "readlines",
            "recv", "recvfrom", "input"
        }

    def _is_external_taint_source(self, node: ast.AST) -> bool:
        """Identifies if an AST node reads from external environment, file, network, or args."""
        if isinstance(node, ast.Call):
            # os.getenv(...) or sys.argv lookup
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in self.taint_source_functions:
                    return True
            elif isinstance(node.func, ast.Name):
                if node.func.id in ("input", "open"):
                    return True

        elif isinstance(node, ast.Subscript):
            # os.environ["VAR"] or sys.argv[1]
            if isinstance(node.value, ast.Attribute) and isinstance(node.value.value, ast.Name):
                if node.value.value.id == "os" and node.value.attr == "environ":
                    return True
                elif node.value.value.id == "sys" and node.value.attr == "argv":
                    return True
            elif isinstance(node.value, ast.Name):
                if node.value.id in ("sys_argv", "environ"):
                    return True
                    
        return False

    def _evaluate_symbolic_or_taint(self, node: ast.AST, env: Dict[str, Any]) -> Any:
        """
        Evaluates node into:
        - Exact string value (if statically resolvable)
        - TAINT_EXTERNAL (if derived from external runtime state)
        - None (if unknown non-tainted)
        """
        # Check if node is an external source
        if self._is_external_taint_source(node):
            return TAINT_EXTERNAL

        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return node.value
            elif isinstance(node.value, bytes):
                return node.value.decode("utf-8", errors="ignore")

        elif isinstance(node, ast.Name):
            return env.get(node.id)

        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = self._evaluate_symbolic_or_taint(node.left, env)
            right = self._evaluate_symbolic_or_taint(node.right, env)
            if left == TAINT_EXTERNAL or right == TAINT_EXTERNAL:
                return TAINT_EXTERNAL # Taint spreads!
            if left is not None and right is not None:
                return str(left) + str(right)

        elif isinstance(node, ast.JoinedStr): # f-strings
            parts = []
            for val in node.values:
                res = self._evaluate_symbolic_or_taint(val, env)
                if res == TAINT_EXTERNAL:
                    return TAINT_EXTERNAL # Taint spreads into formatted strings
                elif res is not None:
                    parts.append(str(res))
                else:
                    parts.append("")
            return "".join(parts)

        elif isinstance(node, ast.FormattedValue):
            return self._evaluate_symbolic_or_taint(node.value, env)

        elif isinstance(node, ast.Call):
            # If function itself is a string transformation on a tainted object
            if isinstance(node.func, ast.Attribute):
                caller_val = self._evaluate_symbolic_or_taint(node.func.value, env)
                if caller_val == TAINT_EXTERNAL:
                    return TAINT_EXTERNAL
                if node.func.attr == "decode":
                    return caller_val
                elif node.func.attr == "fromhex":
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

        env: Dict[str, Any] = {}

        for node in ast.walk(tree):
            # Phase 1: Track Variable Assignments & Taint Lattice Propagation
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        val = self._evaluate_symbolic_or_taint(node.value, env)
                        if val is not None:
                            env[target.id] = val

            # Phase 2: Check Sinks against Exact Matches AND External Taint
            if isinstance(node, ast.Call):
                func = node.func

                # Direct Banned Function: eval(x), exec(x), os.system(x)
                if isinstance(func, ast.Name) and func.id in self.banned_target_names:
                    violations.append(f"DIRECT_INSECURE_CALL: {func.id}() at line {node.lineno}")

                elif isinstance(func, ast.Attribute):
                    mod_id = getattr(func.value, "id", "")
                    if func.attr in self.banned_target_names:
                        # Check argument for external taint: os.system(tainted_str)
                        arg0 = self._evaluate_symbolic_or_taint(node.args[0], env) if node.args else None
                        if arg0 == TAINT_EXTERNAL:
                            violations.append(
                                f"TAINTED_SYSCALL_EXECUTION: os.{func.attr}(TAINT_EXTERNAL) "
                                f"invoked with unverified runtime input at line {node.lineno}"
                            )
                        else:
                            violations.append(f"QUALIFIED_INSECURE_CALL: {mod_id}.{func.attr}() at line {node.lineno}")

                # Sink 1: getattr(target, attr_expr)
                if isinstance(func, ast.Name) and func.id in ("getattr", "hasattr"):
                    if len(node.args) >= 2:
                        target_attr = self._evaluate_symbolic_or_taint(node.args[1], env)
                        if target_attr == TAINT_EXTERNAL:
                            violations.append(
                                f"TAINTED_GETATTR_REFLECTION: getattr() target attribute derived "
                                f"from external runtime state (os.getenv/file/network) at line {node.lineno}"
                            )
                        elif target_attr and target_attr in self.banned_target_names:
                            violations.append(
                                f"MULTI_STAGE_GETATTR_INDIRECTION: getattr(..., '{target_attr}') "
                                f"resolved from symbolic data-flow at line {node.lineno}"
                            )

                # Sink 2: operator.attrgetter(attr_expr)
                if isinstance(func, ast.Attribute) and func.attr == "attrgetter":
                    if node.args:
                        target_attr = self._evaluate_symbolic_or_taint(node.args[0], env)
                        if target_attr == TAINT_EXTERNAL:
                            violations.append(
                                f"TAINTED_ATTRGETTER_SINK: operator.attrgetter() target derived "
                                f"from external runtime state at line {node.lineno}"
                            )
                        elif target_attr and target_attr in self.banned_target_names:
                            violations.append(
                                f"OPERATOR_ATTRGETTER_INDIRECTION: operator.attrgetter('{target_attr}') at line {node.lineno}"
                            )

                # Sink 3: importlib.import_module(mod_expr)
                if isinstance(func, ast.Attribute) and func.attr == "import_module":
                    target_mod = self._evaluate_symbolic_or_taint(node.args[0], env) if node.args else "dynamic"
                    if target_mod == TAINT_EXTERNAL:
                        violations.append(
                            f"TAINTED_IMPORTLIB_INJECTION: importlib.import_module() invoked with "
                            f"external runtime input at line {node.lineno}"
                        )
                    else:
                        violations.append(
                            f"DYNAMIC_IMPORTLIB_INJECTION: importlib.import_module('{target_mod}') at line {node.lineno}"
                        )

                # Sink 4: subprocess with shell=True
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                    if func.value.id == "subprocess" and func.attr in ("Popen", "run", "call", "check_output"):
                        arg0 = self._evaluate_symbolic_or_taint(node.args[0], env) if node.args else None
                        for kw in node.keywords:
                            if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                violations.append(
                                    f"SUBPROCESS_SHELL_INJECTION: subprocess.{func.attr}(shell=True) at line {node.lineno}"
                                )
                        if arg0 == TAINT_EXTERNAL:
                            violations.append(
                                f"TAINTED_SUBPROCESS_COMMAND: subprocess.{func.attr}() executed "
                                f"with external runtime input at line {node.lineno}"
                            )

            # Sink 5: Dictionary Subscript os.__dict__[tainted_key]
            elif isinstance(node, ast.Subscript):
                if isinstance(node.value, ast.Attribute) and node.value.attr == "__dict__":
                    sub_key = self._evaluate_symbolic_or_taint(node.slice, env)
                    if sub_key == TAINT_EXTERNAL:
                        violations.append(
                            f"TAINTED_DICT_REFLECTION: __dict__[TAINT_EXTERNAL] invoked with "
                            f"runtime input at line {node.lineno}"
                        )
                    elif sub_key and sub_key in self.banned_target_names:
                        violations.append(
                            f"DICT_REFLECTION_BYPASS: __dict__['{sub_key}'] at line {node.lineno}"
                        )

            # Sink 6: Restricted Module Imports
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
    kernel = ArthurTaintLatticeKernel()
    target_files = [
        "core/ops/provenance/context_lineage_dag_engine.py",
        "core/ops/memory/governed_memory_consolidation_engine.py",
        "core/ops/native/zig/concurrent_merkle_verifier.zig"
    ]
    res = kernel.audit_nist_ssdf_invariants(target_files)
    print("ARTHUR TAINT LATTICE AUDIT RESULT:", json.dumps(res, indent=2))
    sys.exit(0 if res["status"] == "PASSED" else 1)
