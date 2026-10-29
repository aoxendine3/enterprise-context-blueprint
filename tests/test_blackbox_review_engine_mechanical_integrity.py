"""
Mechanical Integrity Test for BlackboxReviewEngine
==================================================
Verifies that Gate 3 (Flawlessness & Torture Verification) physically executes
candidate artifacts and test suites rather than trusting self-reported flags.
"""

import sys
import os
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core", "ops", "discernment")))
from blackbox_review_engine import BlackboxReviewEngine

def test_blackbox_engine_rejects_broken_code_even_with_torture_passed_true():
    eng = BlackboxReviewEngine()
    tmp_dir = tempfile.mkdtemp()
    eng.GOLDEN_LIST_JSON = os.path.join(tmp_dir, "GOLDEN_LIST.json")
    eng.GOLDEN_LIST_MD = os.path.join(tmp_dir, "GOLDEN_LIST.md")
    eng.ledger = {
        "manifest_version": "1.0.0-SOVEREIGN",
        "golden_list": [],
        "rejected_audit_log": [],
        "total_admitted": 0,
        "total_rejected": 0
    }
    eng.save_ledger = lambda: None

    broken_code = "def multiply(a, b):\n    return a + b\n"
    test_suite = "assert multiply(3, 4) == 12\n"

    admitted, reason = eng.evaluate_candidate({
        "name": "Broken Multiply claiming Pass",
        "classification": "Math",
        "immediate_purpose": "Multiplication",
        "market_metric": "100x",
        "flawlessness_proof": "Self asserted",
        "is_basic": False,
        "serves_immediate_need": True,
        "torture_passed": True,  # Fraudulent claim
        "artifact_source": broken_code,
        "test_source": test_suite
    })

    assert not admitted
    assert "Mechanical test execution failed" in reason

def test_blackbox_engine_admits_valid_code_with_passing_tests():
    eng = BlackboxReviewEngine()
    tmp_dir = tempfile.mkdtemp()
    eng.GOLDEN_LIST_JSON = os.path.join(tmp_dir, "GOLDEN_LIST.json")
    eng.GOLDEN_LIST_MD = os.path.join(tmp_dir, "GOLDEN_LIST.md")
    eng.ledger = {
        "manifest_version": "1.0.0-SOVEREIGN",
        "golden_list": [],
        "rejected_audit_log": [],
        "total_admitted": 0,
        "total_rejected": 0
    }
    eng.save_ledger = lambda: None

    valid_code = "def multiply(a, b):\n    return a * b\n"
    test_suite = "assert multiply(3, 4) == 12\nassert multiply(-2, 5) == -10\n"

    admitted, result = eng.evaluate_candidate({
        "name": "Working Multiply",
        "classification": "Math",
        "immediate_purpose": "Multiplication",
        "market_metric": "100x",
        "flawlessness_proof": "Passed 2 assertions",
        "is_basic": False,
        "serves_immediate_need": True,
        "torture_passed": True,
        "artifact_source": valid_code,
        "test_source": test_suite
    })

    assert admitted
    assert result.startswith("GOLDEN-")

if __name__ == "__main__":
    pytest.main(["-v", __file__])
