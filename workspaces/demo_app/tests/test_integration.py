"""Integration and End-to-End CLI tests for demo_app.

Covers T-E2E-01 through T-E2E-13 and subcommand executions.
Executes real subprocess commands via sys.executable against main.py and -m demo_app.
Zero external dependencies.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_main_script = os.path.join(_project_root, "main.py")


class TestIntegrationCLI(unittest.TestCase):
    """End-to-End integration tests invoking real CLI subprocesses."""

    def _run_cli(self, args: list[str], module_mode: bool = False) -> subprocess.CompletedProcess:
        """Run CLI subprocess with isolated environment and UTF-8 encoding."""
        env = os.environ.copy()
        env["PYTHONPATH"] = _project_root + os.pathsep + env.get("PYTHONPATH", "")
        env["PYTHONIOENCODING"] = "utf-8"

        if module_mode:
            cmd = [sys.executable, "-m", "demo_app"] + args
        else:
            cmd = [sys.executable, _main_script] + args

        return subprocess.run(
            cmd,
            cwd=_project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            env=env,
        )

    def test_e2e_default_invocation(self) -> None:
        """T-E2E-01: Default invocation without args exits 0 and prints greeting & status."""
        proc = self._run_cli([])
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Hello, World!", proc.stdout)
        self.assertIn("SYSTEM STATUS", proc.stdout)
        self.assertIn("Status:", proc.stdout)
        self.assertEqual(proc.stderr.strip(), "")

    def test_e2e_custom_name(self) -> None:
        """T-E2E-02: Custom name flag prints personalized greeting."""
        proc = self._run_cli(["--name", "Alice"])
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Hello, Alice!", proc.stdout)
        self.assertEqual(proc.stderr.strip(), "")

    def test_e2e_style_selection(self) -> None:
        """T-E2E-03: Style selection prints formal greeting."""
        proc = self._run_cli(["--name", "Bob", "--style", "formal"])
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Greetings, Bob. Welcome to the SSOT Agentic Brain.", proc.stdout)
        self.assertEqual(proc.stderr.strip(), "")

    def test_e2e_json_output_mode(self) -> None:
        """T-E2E-04: --json flag outputs strictly valid JSON containing required keys."""
        proc = self._run_cli(["--name", "Charlie", "--json"])
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stderr.strip(), "")

        # Must parse without syntax errors
        data = json.loads(proc.stdout)
        self.assertEqual(data["status"], "success")
        self.assertIn("version", data)
        self.assertIn("timestamp", data)
        self.assertIn("greeting", data)
        self.assertEqual(data["greeting"], "Hello, Charlie!")
        self.assertEqual(data["result"]["target"], "Charlie")

    def test_e2e_calc_plain(self) -> None:
        """T-E2E-05: Calculation in plain text outputs summary metrics."""
        proc = self._run_cli(["--calc", "5, 10, 15, 20"])
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Count:    4", proc.stdout)
        self.assertIn("Sum:      50.0", proc.stdout)
        self.assertIn("Mean:     12.5", proc.stdout)
        self.assertEqual(proc.stderr.strip(), "")

    def test_e2e_calc_with_json(self) -> None:
        """T-E2E-06: Calculation in JSON mode outputs calculation object."""
        proc = self._run_cli(["--calc", "2, 4, 6", "--json"])
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stderr.strip(), "")

        data = json.loads(proc.stdout)
        calc = data["calculation"]
        self.assertEqual(calc["count"], 3)
        self.assertEqual(calc["sum"], 12.0)
        self.assertEqual(calc["mean"], 4.0)
        self.assertEqual(calc["min"], 2.0)
        self.assertEqual(calc["max"], 6.0)

    def test_e2e_combined_name_calc_json(self) -> None:
        """T-E2E-07: Combined name, calc, and JSON flags."""
        proc = self._run_cli(["--name", "Dana", "--calc", "10,20", "--json"])
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stderr.strip(), "")

        data = json.loads(proc.stdout)
        self.assertEqual(data["greeting"], "Hello, Dana!")
        calc = data["calculation"]
        self.assertEqual(calc["count"], 2)
        self.assertEqual(calc["sum"], 30.0)
        self.assertEqual(calc["mean"], 15.0)

    def test_e2e_version_flag(self) -> None:
        """T-E2E-08: --version prints application version string and exits 0."""
        proc = self._run_cli(["--version"])
        self.assertEqual(proc.returncode, 0)
        self.assertIn("demo_app 1.0.0", proc.stdout)

    def test_e2e_help_flag(self) -> None:
        """T-E2E-09: --help prints usage description and exits 0."""
        proc = self._run_cli(["--help"])
        self.assertEqual(proc.returncode, 0)
        self.assertIn("usage:", proc.stdout.lower())
        self.assertIn("--name", proc.stdout)
        self.assertIn("--calc", proc.stdout)
        self.assertIn("--style", proc.stdout)
        self.assertIn("--json", proc.stdout)

    def test_e2e_invalid_flag(self) -> None:
        """T-E2E-10: Unknown CLI flag returns exit code 2 and outputs to stderr."""
        proc = self._run_cli(["--unknown-flag"])
        self.assertEqual(proc.returncode, 2)
        self.assertIn("unrecognized arguments", proc.stderr)

    def test_e2e_missing_flag_value(self) -> None:
        """T-E2E-11: Missing flag value returns exit code 2 and outputs to stderr."""
        proc = self._run_cli(["--name"])
        self.assertEqual(proc.returncode, 2)
        self.assertIn("expected one argument", proc.stderr)

    def test_e2e_malformed_calc_data(self) -> None:
        """T-E2E-12: Non-numeric calc input returns exit code 1 with stderr error."""
        proc = self._run_cli(["--calc", "foo,bar"])
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout.strip(), "")
        self.assertIn("Error: Invalid numeric value 'foo' in --calc argument", proc.stderr)

    def test_e2e_invalid_style_flag(self) -> None:
        """T-E2E-13: Invalid style option returns exit code 2 and stderr error."""
        proc = self._run_cli(["--style", "invalid_style"])
        self.assertEqual(proc.returncode, 2)
        self.assertIn("invalid choice", proc.stderr)

    def test_e2e_subcommand_greet(self) -> None:
        """Subcommand 'greet' executes successfully."""
        proc = self._run_cli(["greet", "--name", "SubTester", "--style", "sovereign"])
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Greetings, SubTester. Xoras Sovereign Core is online and operational.", proc.stdout)

    def test_e2e_subcommand_status_json(self) -> None:
        """Subcommand 'status --system --json' outputs valid telemetry JSON."""
        proc = self._run_cli(["status", "--system", "--json"])
        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertEqual(data["status"], "success")
        self.assertIn("system", data["result"])
        self.assertIn("platform", data["result"]["system"])

    def test_e2e_subcommand_calc_division_by_zero(self) -> None:
        """Subcommand 'calc --op div --args 10 0' returns exit code 1 on division by zero."""
        proc = self._run_cli(["calc", "--op", "div", "--args", "10", "0"])
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Error: Division by zero is undefined", proc.stderr)

    def test_e2e_package_module_execution(self) -> None:
        """Execute via python -m demo_app [args]."""
        proc = self._run_cli(["--name", "ModuleTester", "--json"], module_mode=True)
        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertEqual(data["greeting"], "Hello, ModuleTester!")


if __name__ == "__main__":
    unittest.main()
