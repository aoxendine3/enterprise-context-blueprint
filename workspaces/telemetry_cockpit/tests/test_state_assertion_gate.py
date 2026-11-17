#!/usr/bin/env python3
"""Layer 2 RAW gate tests. Run with: python3 -m unittest discover -s tests -p 'test_*.py'."""

import hashlib
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

GATE_PATH = Path(__file__).resolve().parents[3] / "ops" / "telemetry" / "state_assertion_gate.py"
spec = importlib.util.spec_from_file_location("state_assertion_gate", GATE_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules["state_assertion_gate"] = module
spec.loader.exec_module(module)
Gate = module.StateAssertionGate


class RawGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "artifact.bin")

    def tearDown(self):
        self.tmp.cleanup()

    def test_nonzero_exit_fails_closed(self):
        result = Gate.verify_mutation(self.path, 0, 1, "a" * 64)
        self.assertEqual(result["status"], "FAIL_CLOSED")
        self.assertEqual(result["sdi"], 1.0)

    def test_phantom_file_fails_closed(self):
        result = Gate.verify_mutation(self.path, 0, 0, "a" * 64)
        self.assertEqual(result["status"], "FAIL_CLOSED")
        self.assertIn("Phantom mutation", result["reason"])

    def test_invalid_prehash_fails_closed(self):
        Path(self.path).write_bytes(b"abc")
        for bad in ["", "abc", "A" * 64, "z" * 64]:
            result = Gate.verify_mutation(self.path, 0, 0, bad)
            self.assertEqual(result["status"], "FAIL_CLOSED")

    def test_unchanged_hash_fails_closed(self):
        Path(self.path).write_bytes(b"unchanged")
        digest = hashlib.sha256(b"unchanged").hexdigest()
        result = Gate.verify_mutation(self.path, 0, 0, digest)
        self.assertEqual(result["status"], "FAIL_CLOSED")
        self.assertIn("Illusion of state", result["reason"])

    def test_real_mutation_is_certified(self):
        Path(self.path).write_bytes(b"before")
        before = hashlib.sha256(b"before").hexdigest()
        Path(self.path).write_bytes(b"after")
        result = Gate.verify_mutation(self.path, 0, 0, before)
        self.assertEqual(result["status"], "CERTIFIED")
        self.assertEqual(result["sdi"], 0.0)
        self.assertEqual(result["post_hash"], hashlib.sha256(b"after").hexdigest())

    def test_verify_hash_match_and_mismatch(self):
        Path(self.path).write_bytes(b"payload")
        good = hashlib.sha256(b"payload").hexdigest()
        self.assertEqual(Gate.verify_hash(self.path, good)["status"], "CERTIFIED")
        self.assertEqual(Gate.verify_hash(self.path, "0" * 64)["status"], "FAIL_CLOSED")

    def test_toctou_double_read_fails_closed(self):
        Path(self.path).write_bytes(b"stable")
        original = module._read_file
        calls = {"n": 0}

        def flaky(path):
            calls["n"] += 1
            return b"stable" if calls["n"] == 1 else b"mutated"

        module._read_file = flaky
        try:
            result = Gate.verify_hash(self.path, hashlib.sha256(b"stable").hexdigest())
            self.assertEqual(result["status"], "FAIL_CLOSED")
            self.assertIn("TOCTOU", result["reason"])
        finally:
            module._read_file = original


if __name__ == "__main__":
    unittest.main()
