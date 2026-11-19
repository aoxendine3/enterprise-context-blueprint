#!/usr/bin/env python3
"""Tracked regression tests for the audited Rust AST FFI contract.

Covers the exact findings from AST_FFI_AUDIT_20261119:
  - deep nesting must not crash the host (no unwinding across C ABI)
  - malformed Python must fail closed (never report SAFE)
  - the join/builtins bypass must be vetoed through the FFI
  - native mode must remain a superset of the Python scanner
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "workspaces" / "xoras_agent_framework"))
from xoras.ast_security import ASTSecurityEngine  # noqa: E402

NATIVE = (ROOT / "core" / "native" / "lib" / "libarthur_ast_rs.dylib").is_file()


@unittest.skipUnless(NATIVE, "native dylib not built on this host")
class ArthurAstFfiContract(unittest.TestCase):
    def setUp(self):
        self.native = ASTSecurityEngine(use_native_rust=True)
        self.python = ASTSecurityEngine(use_native_rust=False)

    def test_join_builtins_bypass_is_vetoed(self):
        payload = "fn = ''.join(['ev','al'])\ngetattr(__builtins__, fn)('1+1')"
        self.assertFalse(self.native.scan_code(payload).is_safe)

    def test_deep_nesting_does_not_crash_and_fails_closed(self):
        payload = "x = " + ("(" * 20000) + "1" + (")" * 20000)
        result = self.native.scan_code(payload)
        self.assertFalse(result.is_safe, "deep nesting must be a VETO, never SAFE")

    def test_syntax_errors_fail_closed(self):
        for bad in ("def (:", "ev" + "al(", "if True:\n  x ="):
            with self.subTest(bad=bad):
                self.assertFalse(self.native.scan_code(bad).is_safe)

    def test_native_is_superset_of_python(self):
        payload = "x = globals()['__builtins__']"
        py = self.python.scan_code(payload)
        nat = self.native.scan_code(payload)
        if not py.is_safe:
            self.assertFalse(nat.is_safe, "native must never lose a Python detection")

    def test_long_binary_chain_does_not_crash(self):
        # The auditor's second P0: eval_expression recursed on binary_operator
        # left children without a bound; 50k terms crashed the host.
        payload = "x = " + "+".join(["1"] * 50000)
        result = self.native.scan_code(payload)
        self.assertFalse(result.is_safe, "long binary chain must be VETO, never SAFE")

    def test_clean_code_is_safe(self):
        self.assertTrue(self.native.scan_code("x = 1 + 2\nprint(x)\n").is_safe)


class MissingLibraryFailsLoudly(unittest.TestCase):
    def test_missing_native_library_raises(self):
        import xoras.ast_security as mod
        original = mod.ASTSecurityEngine._load_native_rust
        try:
            mod.ASTSecurityEngine._load_native_rust = classmethod(lambda cls: None)
            eng = mod.ASTSecurityEngine(use_native_rust=True)
            with self.assertRaises(RuntimeError):
                eng.scan_code("x = 1")
        finally:
            mod.ASTSecurityEngine._load_native_rust = original


if __name__ == "__main__":
    unittest.main()
