"""Unit tests for demo_app.processor module.

Covers T-UNIT-10 through T-UNIT-17, diagnostics, health checks, arithmetic,
statistics, Fibonacci sequence, and primality checks.
Zero external dependencies.
"""

from __future__ import annotations

import os
import sys
import unittest

# Ensure demo_app is importable
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from demo_app.processor import (
    check_prime,
    compute_stats,
    execute_arithmetic,
    generate_fibonacci,
    get_system_info,
    get_system_status,
    get_workspace_health,
    parse_number_list,
)


class TestProcessor(unittest.TestCase):
    """Test suite for processor and diagnostic functions."""

    def test_compute_stats_integers(self) -> None:
        """T-UNIT-10: Compute statistics on list of integers."""
        stats = compute_stats([10, 20, 30, 40])
        self.assertEqual(stats["count"], 4)
        self.assertEqual(stats["sum"], 100.0)
        self.assertEqual(stats["mean"], 25.0)
        self.assertEqual(stats["median"], 25.0)
        self.assertEqual(stats["min"], 10.0)
        self.assertEqual(stats["max"], 40.0)
        self.assertAlmostEqual(stats["variance"], 166.66666666666666)

    def test_compute_stats_floats(self) -> None:
        """T-UNIT-11: Compute statistics on float values."""
        stats = compute_stats([1.5, 2.5, 6.0])
        self.assertEqual(stats["count"], 3)
        self.assertEqual(stats["sum"], 10.0)
        self.assertAlmostEqual(stats["mean"], 3.3333333333333335)
        self.assertEqual(stats["min"], 1.5)
        self.assertEqual(stats["max"], 6.0)

    def test_compute_stats_single(self) -> None:
        """T-UNIT-12: Single item list has zero variance and stdev."""
        stats = compute_stats([42])
        self.assertEqual(stats["count"], 1)
        self.assertEqual(stats["sum"], 42.0)
        self.assertEqual(stats["mean"], 42.0)
        self.assertEqual(stats["min"], 42.0)
        self.assertEqual(stats["max"], 42.0)
        self.assertEqual(stats["variance"], 0.0)
        self.assertEqual(stats["std_dev"], 0.0)

    def test_compute_stats_negative(self) -> None:
        """T-UNIT-13: Handle negative and mixed numbers properly."""
        stats = compute_stats([-15, 0, 15])
        self.assertEqual(stats["count"], 3)
        self.assertEqual(stats["sum"], 0.0)
        self.assertEqual(stats["mean"], 0.0)
        self.assertEqual(stats["min"], -15.0)
        self.assertEqual(stats["max"], 15.0)

    def test_compute_stats_empty(self) -> None:
        """T-UNIT-14: Empty list raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            compute_stats([])
        self.assertIn("Cannot compute statistics on empty data", str(ctx.exception))

    def test_parse_number_list_valid(self) -> None:
        """T-UNIT-15: Parse valid comma or space separated strings."""
        result = parse_number_list("1, 2, 3, 4.5")
        self.assertEqual(result, [1.0, 2.0, 3.0, 4.5])

        result2 = parse_number_list("10 20 30")
        self.assertEqual(result2, [10.0, 20.0, 30.0])

    def test_parse_number_list_invalid(self) -> None:
        """T-UNIT-16: Malformed numeric string raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            parse_number_list("1, abc, 3")
        self.assertIn("abc", str(ctx.exception))

    def test_parse_number_list_empty(self) -> None:
        """Empty number string raises ValueError."""
        with self.assertRaises(ValueError):
            parse_number_list("")
        with self.assertRaises(ValueError):
            parse_number_list("   ")

    def test_system_status(self) -> None:
        """T-UNIT-17: Return system status payload with metadata."""
        status = get_system_status()
        self.assertEqual(status["status"], "OK")
        self.assertEqual(status["app_name"], "demo_app")
        self.assertEqual(status["version"], "1.0.0")
        self.assertIn("timestamp", status)

    def test_system_info(self) -> None:
        """Query platform and host environment info."""
        info = get_system_info()
        self.assertIn("os", info)
        self.assertIn("platform", info)
        self.assertIn("python_version", info)
        self.assertIn("cwd", info)
        self.assertIn("node", info)
        self.assertIn("timestamp", info)

    def test_workspace_health_valid(self) -> None:
        """Workspace health inspection on current directory."""
        health = get_workspace_health()
        self.assertTrue(health["accessible"])
        self.assertIn(health["status"], ["HEALTHY", "WARNING_LOW_DISK"])
        self.assertGreater(health["total_bytes"], 0)
        self.assertGreaterEqual(health["free_bytes"], 0)

    def test_workspace_health_invalid_path(self) -> None:
        """Workspace health reports UNHEALTHY when path is inaccessible."""
        health = get_workspace_health("nonexistent_directory_xyz_12345")
        self.assertFalse(health["accessible"])
        self.assertEqual(health["status"], "UNHEALTHY")

    def test_arithmetic_all_ops(self) -> None:
        """Arithmetic operations for add, sub, mul, div, pow, mod."""
        self.assertEqual(execute_arithmetic("add", 10, 5), 15.0)
        self.assertEqual(execute_arithmetic("sub", 10, 5), 5.0)
        self.assertEqual(execute_arithmetic("mul", 10, 5), 50.0)
        self.assertEqual(execute_arithmetic("div", 10, 5), 2.0)
        self.assertEqual(execute_arithmetic("pow", 2, 3), 8.0)
        self.assertEqual(execute_arithmetic("mod", 10, 3), 1.0)

    def test_arithmetic_division_by_zero(self) -> None:
        """Division and modulo by zero raise ZeroDivisionError."""
        with self.assertRaises(ZeroDivisionError):
            execute_arithmetic("div", 10, 0)
        with self.assertRaises(ZeroDivisionError):
            execute_arithmetic("mod", 10, 0)

    def test_arithmetic_unknown_op(self) -> None:
        """Unknown arithmetic operation raises ValueError."""
        with self.assertRaises(ValueError):
            execute_arithmetic("unsupported_op", 10, 5)

    def test_fibonacci_sequence(self) -> None:
        """Fibonacci generator produces correct series."""
        self.assertEqual(generate_fibonacci(1), [0])
        self.assertEqual(generate_fibonacci(2), [0, 1])
        self.assertEqual(generate_fibonacci(7), [0, 1, 1, 2, 3, 5, 8])

    def test_fibonacci_bounds(self) -> None:
        """Fibonacci bounds validation for n < 1 or n > 1000."""
        with self.assertRaises(ValueError):
            generate_fibonacci(0)
        with self.assertRaises(ValueError):
            generate_fibonacci(1001)

    def test_check_prime_prime(self) -> None:
        """Primality check correctly identifies prime numbers."""
        res = check_prime(29)
        self.assertTrue(res["is_prime"])
        self.assertEqual(res["factors"], [1, 29])

    def test_check_prime_composite(self) -> None:
        """Primality check correctly identifies composite numbers with factors."""
        res = check_prime(30)
        self.assertFalse(res["is_prime"])
        self.assertEqual(res["factors"], [1, 2, 3, 5, 6, 10, 15, 30])

    def test_check_prime_one(self) -> None:
        """1 is not prime by mathematical definition."""
        res = check_prime(1)
        self.assertFalse(res["is_prime"])
        self.assertEqual(res["factors"], [1])

    def test_check_prime_invalid(self) -> None:
        """Primality check on n < 1 raises ValueError."""
        with self.assertRaises(ValueError):
            check_prime(0)
        with self.assertRaises(ValueError):
            check_prime(-7)


if __name__ == "__main__":
    unittest.main()
