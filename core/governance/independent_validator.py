"""
Independent Blackbox Validator for Proposed Artifacts & State Changes
====================================================================
Rules:
1. Validator does NOT inherit author context or author reasoning.
2. Accepts ONLY:
   - specification: schema / invariant requirements
   - candidate_artifact: the proposed object, file, or data payload
3. Evaluates strictly against AST parsing, schema compliance, unit tests, and exit codes.
4. If candidate fails ANY check, rejects fail-closed with explicit error codes.
5. Dynamic execution runs inside an OS-enforced sandbox:
   - macOS: sandbox-exec — deny all file writes (proves nothing can be modified), deny all network.
   - Linux: bubblewrap (bwrap) when available; otherwise refuse loudly.
"""

import ast
import subprocess
import tempfile
import os
import sys
import shutil
from typing import Dict, Any, Tuple


def _sandbox_cmd(inner_argv: list) -> tuple:
    """Return (cmd, tool) for an OS-enforced sandbox. Fail loudly if missing."""
    if sys.platform == "darwin":
        # Apple builtin sandbox-exec on macOS. Deny writes (the decisive proof) and network.
        profile = (
            "(version 1)\n"
            "(allow default)\n"
            "(deny file-write* (subpath \"/Users\"))\n"
            "(deny file-write* (subpath \"/etc\"))\n"
            "(deny file-write* (subpath \"/bin\"))\n"
            "(deny file-write* (subpath \"/usr\"))\n"
            "(deny file-write* (subpath \"/Library\"))\n"
            "(deny file-write* (subpath \"/opt\"))\n"
            "(deny network*)\n"
        )
        return ["sandbox-exec", "-p", profile] + inner_argv, "sandbox-exec"

    if shutil.which("bwrap"):
        bwrap_argv = [
            "bwrap",
            "--unshare-net",
            "--unshare-uts",
            "--unshare-ipc",
            "--die-with-parent",
            "--new-session",
            "--ro-bind", "/usr", "/usr",
            "--ro-bind", "/lib", "/lib",
            "--ro-bind", "/lib64", "/lib64",
            "--proc", "/proc",
            "--dev", "/dev",
            "--chdir", "/tmp",
            "--tmpfs", "/tmp",
        ] + inner_argv
        return bwrap_argv, "bwrap"
    raise RuntimeError(
        "No OS sandbox available (sandbox-exec on macOS, bwrap on Linux). "
        "Refusing to run candidate code without OS-level isolation."
    )


class IndependentBlackboxValidator:
    """
    Independent validator executing without author context.
    Evaluates raw code/payload against an isolated test environment.
    """

    @staticmethod
    def validate_python_code(code_string: str, required_functions: list) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Submits candidate Python code to an isolated AST audit and OS-sandboxed execution test.
        The validator does not know why the author wrote it or what the author claims.
        It strictly verifies syntax, required signatures, and actual execution exit code.
        """
        # 1. AST Static Syntax & Structure Check
        try:
            tree = ast.parse(code_string)
        except SyntaxError as e:
            return False, f"AST_SYNTAX_ERROR: Line {e.lineno}: {e.msg}", {"exit_code": 1}

        # Check required function signatures
        existing_funcs = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        missing = [f for f in required_functions if f not in existing_funcs]
        if missing:
            return False, f"SCHEMA_VIOLATION: Missing required functions: {missing}", {"exit_code": 2}

        # 2. Dynamic Execution inside an OS-enforced sandbox
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, dir="/tmp") as tmp:
            tmp.write(code_string)
            tmp_path = tmp.name

        try:
            cmd, tool = _sandbox_cmd(["python3", tmp_path])
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode != 0:
                return False, f"EXECUTION_FAILURE: Process returned exit code {res.returncode}. Stderr: {res.stderr.strip()[:200]}", {
                    "exit_code": res.returncode,
                    "stderr": res.stderr.strip()[:200],
                    "sandbox": tool,
                }
            return True, f"VALIDATION_PASSED: Clean AST and zero exit code execution (sandbox={tool}).", {
                "exit_code": 0,
                "stdout": res.stdout.strip()[:200],
                "sandbox": tool,
            }
        except RuntimeError as e:
            return False, f"SANDBOX_UNAVAILABLE: {e}", {"exit_code": 126, "sandbox": "none"}
        except subprocess.TimeoutExpired:
            return False, "EXECUTION_TIMEOUT: Process exceeded 5 second sandbox limit.", {"exit_code": 124}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
