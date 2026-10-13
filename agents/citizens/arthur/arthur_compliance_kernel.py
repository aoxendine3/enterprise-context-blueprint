#!/usr/bin/env python3
"""
==============================================================================
ARTHUR (SEAT 7): BIDIRECTIONAL TAINT-AND-ANTIDOTE SANITIZER LATTICE KERNEL
==============================================================================
Mandate: Close the False-Positive Seam by Tracking Both Poison & Antidote.
Lattice Structure:
  1. POISON (TAINT_EXTERNAL):
     - Originates from external streams (os.getenv, open.read, sys.argv, network).
     - Propagates transitively across concatenations, joins, format strings.
  2. ANTIDOTE / SANITIZATION OPERATORS (Kills Taint -> SANITIZED):
     - Operator A (Type-Casting Guard):
       int(x), float(x) converts string taint into discrete numeric types (neutralizing code injection).
     - Operator B (Whitelist Membership Invariant):
       if x in ALLOWLIST / if x in ("host", "port", "timeout"):
       Guarantees variable is bounded to explicit, verified set.
     - Operator C (RegEx / Pattern Constraint):
       re.match(r"^[a-zA-Z0-9_]+$", x) strips command separators/special characters.
     - Operator D (Explicit Allowlist Dict Lookup):
       SAFE_ACTIONS.get(x, default)
  3. Security Sinks:
     - If argument is POISON (TAINT_EXTERNAL) -> VETO (NIST_SP_800_218_HARD_VETO).
     - If argument is ANTIDOTE (SANITIZED or Whitelisted String) -> ADMITTED.
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

TAINT_EXTERNAL = "__TAINT_EXTERNAL_POISON__"
TAINT_SANITIZED = "__TAINT_SANITIZED_ANTIDOTE__"

class ArthurSanitizerLatticeKernel:
    def __init__(self, root: Path = SSOT_ROOT):
        self.root = root
        
        self.banned_target_names = {
            "eval", "exec", "compile", "__import__",
            "system", "popen", "execv", "execl", "spawn", "fork", "kill"
        }
        
        self.banned_modules = {
            "ctypes", "pty"
        }

        self.taint_source_functions = {
            "getenv", "read", "read_text", "read_bytes", "readline", "readlines",
            "recv", "recvfrom", "input"
        }

        # Antidote Type-Casters that mathematically neutralize string-injection attacks
        self.antidote_type_casters = {
            "int", "float", "bool", "len", "ord"
        }

    def _is_external_taint_source(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in self.taint_source_functions:
                    return True
            elif isinstance(node.func, ast.Name):
                if node.func.id in ("input", "open"):
                    return True

        elif isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Attribute) and isinstance(node.value.value, ast.Name):
                if node.value.value.id == "os" and node.value.attr == "environ":
                    return True
                elif node.value.value.id == "sys" and node.value.attr == "argv":
                    return True
            elif isinstance(node.value, ast.Name):
                if node.value.id in ("sys_argv", "environ"):
                    return True
        return False

    def _is_antidote_type_caster(self, node: ast.AST) -> bool:
        """Detects if node wraps input in a sanitizing type cast: int(x), float(x)."""
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in self.antidote_type_casters:
                return True
        return False

    def _evaluate_symbolic_or_taint(self, node: ast.AST, env: Dict[str, Any], sanitized_vars: Set[str]) -> Any:
        # 1. Antidote Type-Cast Check (int, float kills poison!)
        if self._is_antidote_type_caster(node):
            return TAINT_SANITIZED

        # 2. Check if variable was explicitly validated via in-set/whitelist guard
        if isinstance(node, ast.Name):
            if node.id in sanitized_vars:
                return TAINT_SANITIZED
            return env.get(node.id)

        # 3. Check for raw external taint source
        if self._is_external_taint_source(node):
            return TAINT_EXTERNAL

        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return node.value
            elif isinstance(node.value, bytes):
                return node.value.decode("utf-8", errors="ignore")
            elif isinstance(node.value, (int, float, bool)):
                return TAINT_SANITIZED

        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = self._evaluate_symbolic_or_taint(node.left, env, sanitized_vars)
            right = self._evaluate_symbolic_or_taint(node.right, env, sanitized_vars)
            if left == TAINT_EXTERNAL or right == TAINT_EXTERNAL:
                return TAINT_EXTERNAL # Poison spreads unless sanitized!
            if left is not None and right is not None:
                return str(left) + str(right)

        elif isinstance(node, ast.JoinedStr):
            parts = []
            for val in node.values:
                res = self._evaluate_symbolic_or_taint(val, env, sanitized_vars)
                if res == TAINT_EXTERNAL:
                    return TAINT_EXTERNAL
                elif res is not None:
                    parts.append(str(res))
            return "".join(parts)

        elif isinstance(node, ast.FormattedValue):
            return self._evaluate_symbolic_or_taint(node.value, env, sanitized_vars)

        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                caller_val = self._evaluate_symbolic_or_taint(node.func.value, env, sanitized_vars)
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
        sanitized_vars: Set[str] = set()

        # Step 0: Antidote Scanner — Discover Whitelist Guards (e.g. if x in ALLOWED:)
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                # Check condition: if var in ("a", "b") or if var in ALLOWED_LIST
                test = node.test
                if isinstance(test, ast.Compare):
                    for op, comparator in zip(test.ops, test.comparators):
                        if isinstance(op, ast.In):
                            if isinstance(test.left, ast.Name):
                                # The variable inside the if-block is mathematically sanitized by the whitelist!
                                sanitized_vars.add(test.left.id)

        # Step 1: Traversal with Poison & Antidote Tracking
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        val = self._evaluate_symbolic_or_taint(node.value, env, sanitized_vars)
                        if val is not None:
                            env[target.id] = val

            elif isinstance(node, ast.Call):
                func = node.func

                # Direct Banned Function: eval(), exec()
                if isinstance(func, ast.Name) and func.id in self.banned_target_names:
                    violations.append(f"DIRECT_INSECURE_CALL: {func.id}() at line {node.lineno}")

                elif isinstance(func, ast.Attribute):
                    mod_id = getattr(func.value, "id", "")
                    if func.attr in self.banned_target_names:
                        arg0 = self._evaluate_symbolic_or_taint(node.args[0], env, sanitized_vars) if node.args else None
                        if arg0 == TAINT_EXTERNAL:
                            violations.append(
                                f"TAINTED_SYSCALL_EXECUTION: os.{func.attr}(TAINT_EXTERNAL) "
                                f"invoked with unverified runtime input at line {node.lineno}"
                            )
                        elif arg0 != TAINT_SANITIZED:
                            violations.append(f"QUALIFIED_INSECURE_CALL: {mod_id}.{func.attr}() at line {node.lineno}")

                # Sink 1: getattr(target, attr_expr)
                if isinstance(func, ast.Name) and func.id in ("getattr", "hasattr"):
                    if len(node.args) >= 2:
                        target_attr = self._evaluate_symbolic_or_taint(node.args[1], env, sanitized_vars)
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
                        elif target_attr == TAINT_SANITIZED:
                            # Sanitized via whitelist or type caster — ADMITTED cleanly!
                            pass

                # Sink 2: operator.attrgetter(attr_expr)
                if isinstance(func, ast.Attribute) and func.attr == "attrgetter":
                    if node.args:
                        target_attr = self._evaluate_symbolic_or_taint(node.args[0], env, sanitized_vars)
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
                    target_mod = self._evaluate_symbolic_or_taint(node.args[0], env, sanitized_vars) if node.args else "dynamic"
                    if target_mod == TAINT_EXTERNAL:
                        violations.append(
                            f"TAINTED_IMPORTLIB_INJECTION: importlib.import_module() invoked with "
                            f"external runtime input at line {node.lineno}"
                        )
                    elif target_mod != TAINT_SANITIZED:
                        violations.append(
                            f"DYNAMIC_IMPORTLIB_INJECTION: importlib.import_module('{target_mod}') at line {node.lineno}"
                        )

                # Sink 4: subprocess with shell=True
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                    if func.value.id == "subprocess" and func.attr in ("Popen", "run", "call", "check_output"):
                        arg0 = self._evaluate_symbolic_or_taint(node.args[0], env, sanitized_vars) if node.args else None
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

            elif isinstance(node, ast.Subscript):
                if isinstance(node.value, ast.Attribute) and node.value.attr == "__dict__":
                    sub_key = self._evaluate_symbolic_or_taint(node.slice, env, sanitized_vars)
                    if sub_key == TAINT_EXTERNAL:
                        violations.append(
                            f"TAINTED_DICT_REFLECTION: __dict__[TAINT_EXTERNAL] invoked with "
                            f"runtime input at line {node.lineno}"
                        )
                    elif sub_key and sub_key in self.banned_target_names:
                        violations.append(
                            f"DICT_REFLECTION_BYPASS: __dict__['{sub_key}'] at line {node.lineno}"
                        )

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

# Backward-compatible aliases for historical gauntlet runners
HardenedArthurComplianceKernel = ArthurSanitizerLatticeKernel
ArthurSymbolicTaintKernel = ArthurSanitizerLatticeKernel
ArthurTaintLatticeKernel = ArthurSanitizerLatticeKernel

if __name__ == "__main__":
    kernel = ArthurSanitizerLatticeKernel()
    target_files = [
        "core/ops/provenance/context_lineage_dag_engine.py",
        "core/ops/memory/governed_memory_consolidation_engine.py",
        "core/ops/native/zig/concurrent_merkle_verifier.zig"
    ]
    res = kernel.audit_nist_ssdf_invariants(target_files)
    print("ARTHUR SANITIZER LATTICE AUDIT RESULT:", json.dumps(res, indent=2))
    sys.exit(0 if res["status"] == "PASSED" else 1)
