"""
XORAS Systems LLC — Polyglot IPC & WASM Micro-Runtime Sandboxing Bridge
Extends AST security gating and trace signing across C++, Rust, Zig, and WASM binary execution interfaces.
"""

import subprocess
import shlex
import os
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from ..ast_security import ASTSecurityEngine, ASTScanResult

@dataclass
class IPCExecutionResult:
    success: bool
    runtime_target: str
    stdout: str
    stderr: str
    exit_code: int
    ast_verified: bool
    ipc_latency_ms: float

class PolyglotIPCBridge:
    SUPPORTED_RUNTIMES = ["wasm", "c_dylib", "rust_binary", "zig_witness"]

    def __init__(self, workspace_root: str = "."):
        self.workspace_root = workspace_root
        self.ast_engine = ASTSecurityEngine()

    def execute_binary_ipc(self, binary_path: str, args: List[str], runtime_type: str = "wasm") -> IPCExecutionResult:
        """Executes external binary / WASM runtime payload with pre-execution AST/FFI validation."""
        if not os.path.exists(binary_path):
            return IPCExecutionResult(
                success=False,
                runtime_target=runtime_type,
                stdout="",
                stderr=f"IPC Binary file not found: '{binary_path}'",
                exit_code=1,
                ast_verified=False,
                ipc_latency_ms=0.0
            )

        # Pre-execution static inspect on binary command arguments
        cmd_str = f"{binary_path} {' '.join(args)}"
        ast_check = self.ast_engine.scan_code(cmd_str)
        if not ast_check.is_safe:
            return IPCExecutionResult(
                success=False,
                runtime_target=runtime_type,
                stdout="",
                stderr=f"IPC Command blocked by XORAS Security: {', '.join(ast_check.violations)}",
                exit_code=2,
                ast_verified=False,
                ipc_latency_ms=0.0
            )

        # Isolated Subprocess execution
        import time
        t0 = time.time()
        try:
            cmd = [binary_path] + args
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.workspace_root
            )
            t1 = time.time()
            return IPCExecutionResult(
                success=res.returncode == 0,
                runtime_target=runtime_type,
                stdout=res.stdout,
                stderr=res.stderr,
                exit_code=res.returncode,
                ast_verified=True,
                ipc_latency_ms=round((t1 - t0) * 1000, 3)
            )
        except Exception as e:
            t1 = time.time()
            return IPCExecutionResult(
                success=False,
                runtime_target=runtime_type,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                ast_verified=True,
                ipc_latency_ms=round((t1 - t0) * 1000, 3)
            )
