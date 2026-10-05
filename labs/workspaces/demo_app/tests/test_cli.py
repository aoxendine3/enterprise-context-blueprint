"""Unit tests for demo_app.cli module.

Covers T-UNIT-18 through T-UNIT-22, parser construction, flag handling,
subcommands, in-memory CLI execution, and exit codes.
Zero external dependencies.
"""

from __future__ import annotations

import io
import os
import sys
import unittest
from unittest.mock import patch

# Ensure demo_app is importable
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from demo_app.cli import build_parser, main


class TestCLI(unittest.TestCase):
    """Test suite for command-line parser and dispatch logic."""

    def setUp(self) -> None:
        self.parser = build_parser()

    def test_arg_parser_defaults(self) -> None:
        """T-UNIT-18: Default parser values with empty argument list."""
        args = self.parser.parse_args([])
        self.assertIsNone(args.name)
        self.assertEqual(args.style, "standard")
        self.assertIsNone(args.calc)
        self.assertFalse(args.json)
        self.assertIsNone(args.subcommand)

    def test_arg_parser_custom_name(self) -> None:
        """T-UNIT-19: Custom name argument parsing."""
        args = self.parser.parse_args(["--name", "Dev"])
        self.assertEqual(args.name, "Dev")

    def test_arg_parser_calc_flag(self) -> None:
        """T-UNIT-20: Calculation list flag parsing."""
        args = self.parser.parse_args(["--calc", "10,20,30"])
        self.assertEqual(args.calc, "10,20,30")

    def test_arg_parser_json_flag(self) -> None:
        """T-UNIT-21: JSON flag parsing."""
        args = self.parser.parse_args(["--json"])
        self.assertTrue(args.json)

    def test_arg_parser_invalid_flag(self) -> None:
        """T-UNIT-22: Invalid option triggers SystemExit with code 2."""
        with patch("sys.stderr", new_callable=io.StringIO):
            with self.assertRaises(SystemExit) as ctx:
                self.parser.parse_args(["--invalid-option"])
            self.assertEqual(ctx.exception.code, 2)

    def test_subcommand_greet_parsing(self) -> None:
        """Subcommand 'greet' parses flags correctly."""
        args = self.parser.parse_args(["greet", "--name", "Alice", "--style", "casual"])
        self.assertEqual(args.subcommand, "greet")
        self.assertEqual(args.name, "Alice")
        self.assertEqual(args.style, "casual")

    def test_subcommand_status_parsing(self) -> None:
        """Subcommand 'status' parses diagnostic flags."""
        args = self.parser.parse_args(["status", "--system", "--health"])
        self.assertEqual(args.subcommand, "status")
        self.assertTrue(args.system)
        self.assertTrue(args.health)

    def test_subcommand_calc_parsing(self) -> None:
        """Subcommand 'calc' parses arithmetic flags."""
        args = self.parser.parse_args(["calc", "--op", "add", "--args", "10", "20"])
        self.assertEqual(args.subcommand, "calc")
        self.assertEqual(args.op, "add")
        self.assertEqual(args.args, [10.0, 20.0])

    def test_main_default_execution(self) -> None:
        """Default execution without args returns 0."""
        with patch("sys.stdout", new_callable=io.StringIO) as fake_out:
            exit_code = main([])
            self.assertEqual(exit_code, 0)
            self.assertIn("Hello, World!", fake_out.getvalue())

    def test_main_greeting_with_json(self) -> None:
        """main() with --name and --json outputs valid JSON and returns 0."""
        with patch("sys.stdout", new_callable=io.StringIO) as fake_out:
            exit_code = main(["--name", "Tester", "--json"])
            self.assertEqual(exit_code, 0)
            output = fake_out.getvalue()
            self.assertIn('"status": "success"', output)
            self.assertIn('"greeting": "Hello, Tester!"', output)

    def test_main_calc_success(self) -> None:
        """main() with valid --calc returns 0."""
        with patch("sys.stdout", new_callable=io.StringIO) as fake_out:
            exit_code = main(["--calc", "10,20,30"])
            self.assertEqual(exit_code, 0)
            self.assertIn("Mean:", fake_out.getvalue())

    def test_main_calc_domain_error(self) -> None:
        """main() with malformed numbers returns exit code 1."""
        with patch("sys.stderr", new_callable=io.StringIO) as fake_err:
            exit_code = main(["--calc", "foo,bar"])
            self.assertEqual(exit_code, 1)
            self.assertIn("Error: Invalid numeric value 'foo' in --calc argument", fake_err.getvalue())

    def test_main_zero_division_error(self) -> None:
        """main() with division by zero returns exit code 1."""
        with patch("sys.stderr", new_callable=io.StringIO) as fake_err:
            exit_code = main(["calc", "--op", "div", "--args", "10", "0"])
            self.assertEqual(exit_code, 1)
            self.assertIn("Error: Division by zero is undefined", fake_err.getvalue())

    def test_main_invalid_argument_syntax(self) -> None:
        """main() with unrecognized argument returns exit code 2."""
        with patch("sys.stderr", new_callable=io.StringIO):
            exit_code = main(["--unrecognized-argument-xyz"])
            self.assertEqual(exit_code, 2)


if __name__ == "__main__":
    unittest.main()
