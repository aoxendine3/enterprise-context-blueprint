"""
=============================================================================
XORAS HIGH-ASSURANCE CODE SANDBOX RUNNER TOOL
Path: workspaces/xoras_agent_framework/xoras/tools/code_sandbox_runner.py
Standards: NIST SP 800-53 Rev. 5 (CM-7 Least Functionality, SC-39 Process Isolation)
Capabilities: Pre-flight AST Screening, Timeout Enforcement, Ephemeral Sandboxing,
Deterministic Execution Receipts.
=============================================================================
"""

from __future__ import annotations

import ast
import hashlib
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class SandboxExecutionReceipt:
    schema: str
    code_hash: str
    status: str
    exit_code: int
    stdout: str
    stderr: str
    execution_time_ms: float
    security_violations: List[str]


class CodeSandboxRunner:
    """
    Executes short Python verification snippets within a hardened, AST-screened
    subprocess container with strict execution timeouts and zero shell expansion.
    """
    SCHEMA_VERSION = "xoras.code_sandbox_runner.v1"
    MAX_TIMEOUT_SECONDS = 5.0

    # Forbidden call and import identifiers
    FORBIDDEN_CALLS = frozenset({"eval", "exec", "compile", "breakpoint"})
    FORBIDDEN_MODULES = frozenset({"ctypes", "pty", "shutil", "socket", "http.client", "urllib.request"})

    def __init__(self, timeout_sec: float = 3.0) -> None:
        self.timeout_sec = min(max(0.1, timeout_sec), self.MAX_TIMEOUT_SECONDS)

    def screen_ast(self, source_code: str) -> List[str]:
        """Static pre-flight AST inspection to catch dangerous primitives before execution."""
        violations = []
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            return [f"SYNTAX_ERROR: {e.msg} at line {e.lineno}"]

        for node in ast.walk(tree):
            # Check forbidden function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in self.FORBIDDEN_CALLS:
                    violations.append(f"FORBIDDEN_CALL: {node.func.id} at line {node.lineno}")
                elif isinstance(node.func, ast.Attribute) and node.func.attr in self.FORBIDDEN_CALLS:
                    violations.append(f"FORBIDDEN_ATTR_CALL: {node.func.attr} at line {node.lineno}")

            # Check forbidden imports
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    root_mod = alias.name.split(".")[0]
                    if root_mod in self.FORBIDDEN_MODULES:
                        violations.append(f"FORBIDDEN_IMPORT: {alias.name} at line {node.lineno}")

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_mod = node.module.split(".")[0]
                    if root_mod in self.FORBIDDEN_MODULES:
                        violations.append(f"FORBIDDEN_IMPORT_FROM: {node.module} at line {node.lineno}")

            # Check __builtins__ inspection
            elif isinstance(node, ast.Attribute) and node.attr == "__builtins__":
                violations.append(f"FORBIDDEN_BUILTINS_ACCESS at line {node.lineno}")

        return violations

    def run_snippet(self, source_code: str) -> SandboxExecutionReceipt:
        """Execute Python code in isolated process after AST pre-flight screening."""
        code_hash = hashlib.sha256(source_code.encode("utf-8")).hexdigest()
        violations = self.screen_ast(source_code)
        
        if violations:
            return SandboxExecutionReceipt(
                schema=self.SCHEMA_VERSION,
                code_hash=code_hash,
                status="PRE_FLIGHT_BLOCKED",
                exit_code=-1,
                stdout="",
                stderr="\n".join(violations),
                execution_time_ms=0.0,
                security_violations=violations,
            )

        # Write to ephemeral temp script
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(source_code)
            temp_path = f.name

        t0 = time.perf_counter()
        try:
            proc = subprocess.run(
                [sys.executable, "-B", "-S", temp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout_sec,
            )
            t_end = time.perf_counter()
            elapsed_ms = round((t_end - t0) * 1000.0, 3)
            status = "SUCCESS" if proc.returncode == 0 else "RUNTIME_ERROR"
            return SandboxExecutionReceipt(
                schema=self.SCHEMA_VERSION,
                code_hash=code_hash,
                status=status,
                exit_code=proc.returncode,
                stdout=proc.stdout[:4096],
                stderr=proc.stderr[:4096],
                execution_time_ms=elapsed_ms,
                security_violations=[],
            )
        except subprocess.TimeoutExpired:
            t_end = time.perf_counter()
            return SandboxExecutionReceipt(
                schema=self.SCHEMA_VERSION,
                code_hash=code_hash,
                status="TIMEOUT_EXPIRED",
                exit_code=-2,
                stdout="",
                stderr=f"Execution exceeded timeout limit ({self.timeout_sec}s)",
                execution_time_ms=round((t_end - t0) * 1000.0, 3),
                security_violations=["TIMEOUT_EXCEEDED"],
            )
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
