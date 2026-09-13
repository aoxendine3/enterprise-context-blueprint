"""Demonstration Application Test Runner.

Executes all unit and integration test suites, aggregating execution time
and pass/fail metrics.
Zero external dependencies. Compatible with Python 3 standard library.
"""

from __future__ import annotations

import os
import sys
import time
import unittest


def main() -> int:
    """Run all discovered test suites and output structured summary.

    Returns:
        Exit code: 0 if all tests pass, 1 if any failure or error occurs.
    """
    start_time = time.perf_counter()
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    print("=" * 65)
    print("  SSOT DEMONSTRATION APPLICATION — TEST & VERIFICATION SUITE")
    print(f"  Python Interpreter: {sys.executable}")
    print(f"  Project Root:       {project_root}")
    print("=" * 65)

    loader = unittest.defaultTestLoader
    test_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(test_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    passed = total_tests - failures - errors - skipped

    print("\n" + "=" * 65)
    print("  TEST VERIFICATION SUMMARY")
    print("=" * 65)
    print(f"  Total Tests Run:  {total_tests}")
    print(f"  Passed:           {passed}")
    print(f"  Failed:           {failures}")
    print(f"  Errors:           {errors}")
    print(f"  Skipped:          {skipped}")
    print(f"  Total Duration:   {elapsed_ms:.2f} ms")
    print("=" * 65)

    if not result.wasSuccessful():
        print("[FAIL] Test suite failed with errors or failures.")
        return 1

    print("[SUCCESS] All test cases passed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
