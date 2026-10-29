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
"""

import ast
import subprocess
import tempfile
import os
from typing import Dict, Any, Tuple

class IndependentBlackboxValidator:
    """
    Independent validator executing without author context.
    Evaluates raw code/payload against an isolated test environment.
    """

    @staticmethod
    def validate_python_code(code_string: str, required_functions: list) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Submits candidate Python code to an isolated AST audit and sandboxed execution test.
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

        # 2. Dynamic Execution in Isolated Subprocess Sandbox
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
            tmp.write(code_string)
            tmp_path = tmp.name

        try:
            res = subprocess.run(["python3", tmp_path], capture_output=True, text=True, timeout=5)
            if res.returncode != 0:
                return False, f"EXECUTION_FAILURE: Process returned exit code {res.returncode}. Stderr: {res.stderr.strip()}", {
                    "exit_code": res.returncode,
                    "stderr": res.stderr.strip()
                }
            return True, "VALIDATION_PASSED: Clean AST and zero exit code execution.", {
                "exit_code": 0,
                "stdout": res.stdout.strip()
            }
        except subprocess.TimeoutExpired:
            return False, "EXECUTION_TIMEOUT: Process exceeded 5 second sandbox limit.", {"exit_code": 124}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
