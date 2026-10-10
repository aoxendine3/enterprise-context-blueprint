"""
Unit tests for XORAS AST Security Engine.
"""

import pytest
from xoras.ast_security import ASTSecurityEngine

def test_ast_safe_code():
    engine = ASTSecurityEngine()
    code = """
def calculate_sum(a, b):
    return a + b

print(calculate_sum(10, 20))
"""
    result = engine.scan_code(code)
    assert result.is_safe is True
    assert result.safety_score == 1.0
    assert len(result.violations) == 0

def test_ast_forbidden_eval():
    engine = ASTSecurityEngine()
    code = """
x = 10
eval("print(x)")
"""
    result = engine.scan_code(code)
    assert result.is_safe is False
    assert any("eval()" in v for v in result.violations)

def test_ast_forbidden_exec():
    engine = ASTSecurityEngine()
    code = """
exec("import os; os.system('ls')")
"""
    result = engine.scan_code(code)
    assert result.is_safe is False
    assert any("exec()" in v for v in result.violations)

def test_ast_secret_leak_detection():
    engine = ASTSecurityEngine()
    code = """
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
"""
    result = engine.scan_code(code)
    assert result.is_safe is False
    assert len(result.secrets_detected) > 0
