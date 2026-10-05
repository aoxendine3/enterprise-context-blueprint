"""CLI module for SSOT Demonstration Application.

Provides argument parsing, subcommand routing, structured JSON formatting,
and clean exit code discipline (0=success, 1=operational error, 2=CLI error).
Zero external dependencies.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from typing import Any, Dict, List, Optional

from demo_app import __app_name__, __version__
from demo_app.greeting import VALID_STYLES, generate_greeting
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


def _reconfigure_streams() -> None:
    """Safely configure stdout and stderr to UTF-8 on Windows and other platforms."""
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass


def build_parser() -> argparse.ArgumentParser:
    """Construct the command line interface argument parser.

    Returns:
        Configured argparse.ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="demo_app",
        description="SSOT Demonstration Application — Pure Python 3 CLI showcasing sovereign capabilities.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  demo_app                                     # Default greeting and system status\n"
            "  demo_app --name Anthony                      # Custom greeting\n"
            "  demo_app --name Anthony --style formal       # Formal greeting\n"
            "  demo_app --calc '10, 20, 30, 40' --json      # Statistical computation with JSON\n"
            "  demo_app greet --name Alice --style casual   # Greet subcommand\n"
            "  demo_app status --system --json              # System diagnostics\n"
            "  demo_app calc --op div --args 100 5          # Arithmetic operation\n"
        ),
    )

    # Global flags
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"{__app_name__} {__version__}",
        help="Show application version and exit.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Format output as strictly valid JSON.",
    )

    # Top-level direct options for convenience and compatibility
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Name of the person or entity to greet.",
    )
    parser.add_argument(
        "--style",
        type=str,
        default="standard",
        choices=sorted(VALID_STYLES),
        help="Greeting tone style (standard, formal, casual, sovereign, enthusiastic).",
    )
    parser.add_argument(
        "--template",
        type=str,
        default=None,
        help="Custom greeting message template string supporting {name}, {date}, {time}.",
    )
    parser.add_argument(
        "--calc",
        type=str,
        default=None,
        help="Comma or space-separated list of numbers for statistical analysis.",
    )
    parser.add_argument(
        "--stats",
        type=str,
        default=None,
        help="Alias for --calc.",
    )
    parser.add_argument(
        "--op",
        type=str,
        default=None,
        choices=["add", "sub", "mul", "div", "pow", "mod"],
        help="Arithmetic operation to perform.",
    )
    parser.add_argument(
        "--args",
        type=float,
        nargs=2,
        default=None,
        metavar=("A", "B"),
        help="Two numeric operands for the arithmetic operation specified by --op.",
    )
    parser.add_argument(
        "--fib",
        type=int,
        default=None,
        help="Generate the first N Fibonacci numbers (1 <= N <= 1000).",
    )
    parser.add_argument(
        "--prime",
        type=int,
        default=None,
        help="Test if N is prime and compute its factors (N >= 1).",
    )
    parser.add_argument(
        "--system",
        action="store_true",
        default=False,
        help="Query and display system environment diagnostics.",
    )
    parser.add_argument(
        "--health",
        action="store_true",
        default=False,
        help="Inspect workspace accessibility and storage health.",
    )

    # Subcommands
    subparsers = parser.add_subparsers(
        dest="subcommand",
        title="Subcommands",
        description="Optional focused subcommands for specific subsystems.",
    )

    # greet subcommand
    greet_parser = subparsers.add_parser(
        "greet",
        help="Generate greetings with configurable styles and templates.",
    )
    greet_parser.add_argument(
        "name_pos",
        nargs="?",
        default=None,
        help="Optional positional recipient name.",
    )
    greet_parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Name of the person or entity to greet.",
    )
    greet_parser.add_argument(
        "--style",
        type=str,
        default="standard",
        choices=sorted(VALID_STYLES),
        help="Greeting tone style.",
    )
    greet_parser.add_argument(
        "--template",
        type=str,
        default=None,
        help="Custom template string.",
    )
    greet_parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Format output as strictly valid JSON.",
    )

    # status subcommand
    status_parser = subparsers.add_parser(
        "status",
        help="System environment diagnostics and workspace health.",
    )
    status_parser.add_argument(
        "--system",
        action="store_true",
        default=False,
        help="Report system and host telemetry.",
    )
    status_parser.add_argument(
        "--health",
        action="store_true",
        default=False,
        help="Report workspace storage health.",
    )
    status_parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Custom workspace directory path to inspect.",
    )
    status_parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Format output as strictly valid JSON.",
    )

    # calc subcommand
    calc_parser = subparsers.add_parser(
        "calc",
        help="Perform arithmetic, statistical, or algorithmic computations.",
    )
    calc_parser.add_argument(
        "--calc",
        type=str,
        default=None,
        help="Comma-separated numbers for statistical calculation.",
    )
    calc_parser.add_argument(
        "--stats",
        type=str,
        default=None,
        help="Alias for --calc.",
    )
    calc_parser.add_argument(
        "--op",
        type=str,
        default=None,
        choices=["add", "sub", "mul", "div", "pow", "mod"],
        help="Arithmetic operation.",
    )
    calc_parser.add_argument(
        "--args",
        type=float,
        nargs=2,
        default=None,
        metavar=("A", "B"),
        help="Two operands for arithmetic operation.",
    )
    calc_parser.add_argument(
        "--fib",
        type=int,
        default=None,
        help="Generate first N Fibonacci numbers.",
    )
    calc_parser.add_argument(
        "--prime",
        type=int,
        default=None,
        help="Test primality and compute factors for N.",
    )
    calc_parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Format output as strictly valid JSON.",
    )

    return parser


def format_json_envelope(
    command: str,
    result: Dict[str, Any],
    greeting: Optional[str] = None,
    calculation: Optional[Dict[str, Any]] = None,
) -> str:
    """Construct a standardized, strictly valid JSON envelope.

    Args:
        command: Name of command or action executed.
        result: Primary domain result payload.
        greeting: Optional top-level greeting string for convenience.
        calculation: Optional top-level calculation dictionary.

    Returns:
        Formatted JSON string with indentation.
    """
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    envelope: Dict[str, Any] = {
        "status": "success",
        "command": command,
        "timestamp": now_utc.isoformat(),
        "version": __version__,
        "result": result,
        "metadata": {
            "app": __app_name__,
            "version": __version__,
        },
    }
    if greeting is not None:
        envelope["greeting"] = greeting
    if calculation is not None:
        envelope["calculation"] = calculation

    return json.dumps(envelope, indent=2)


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI execution entrypoint.

    Args:
        argv: Command-line arguments. Defaults to sys.argv[1:].

    Returns:
        Exit code: 0 for success, 1 for operational error, 2 for CLI syntax error.
    """
    _reconfigure_streams()
    parser = build_parser()

    # If argv is not provided, use sys.argv[1:]
    if argv is None:
        argv = sys.argv[1:]

    try:
        args = parser.parse_args(argv)
    except SystemExit as se:
        # Re-raise SystemExit so argparse exit codes (e.g. 2 on invalid flags, 0 on --help) are honored
        return int(se.code) if se.code is not None else 2

    is_json = bool(getattr(args, "json", False))

    # Resolve active parameters across top-level and subcommands
    subcmd = getattr(args, "subcommand", None)

    name: Optional[str] = getattr(args, "name", None)
    if subcmd == "greet":
        name_pos = getattr(args, "name_pos", None)
        if name_pos:
            name = name_pos
        elif getattr(args, "name", None):
            name = getattr(args, "name", None)

    style = getattr(args, "style", "standard") or "standard"
    template = getattr(args, "template", None)

    calc_str = getattr(args, "calc", None) or getattr(args, "stats", None)
    op = getattr(args, "op", None)
    op_args = getattr(args, "args", None)
    fib_n = getattr(args, "fib", None)
    prime_n = getattr(args, "prime", None)

    system_flag = bool(getattr(args, "system", False))
    health_flag = bool(getattr(args, "health", False))
    target_path = getattr(args, "path", None)

    # Detect if any specific action was requested
    has_specific_action = (
        subcmd is not None
        or name is not None
        or style != "standard"
        or template is not None
        or calc_str is not None
        or op is not None
        or fib_n is not None
        or prime_n is not None
        or system_flag
        or health_flag
    )

    try:
        # Case 1: Default summary mode when invoked without specific actions
        if not has_specific_action:
            greeting_str = generate_greeting(name=None, style="standard")
            status_info = get_system_status()
            sys_info = get_system_info()
            health_info = get_workspace_health()

            if is_json:
                result_payload = {
                    "greeting": greeting_str,
                    "target": "World",
                    "style": "standard",
                    "system_status": status_info,
                    "system_info": sys_info,
                    "workspace_health": health_info,
                }
                print(format_json_envelope(command="default_summary", result=result_payload, greeting=greeting_str))
                return 0
            else:
                print("=" * 60)
                print(f"       SSOT DEMONSTRATION APPLICATION ({__app_name__} v{__version__})")
                print("=" * 60)
                print(f"\n[GREETING]\n  {greeting_str} Welcome to the SSOT Agentic Brain demo.")
                print(f"\n[SYSTEM STATUS]\n  Status:     {status_info.get('status')}")
                print(f"  Platform:   {sys_info.get('platform')} (Python {sys_info.get('python_version')})")
                print(f"  Node:       {sys_info.get('node')}")
                print(f"  WorkingDir: {sys_info.get('cwd')}")
                print(f"  Disk:       {health_info.get('free_gb', 0)} GB free of {health_info.get('total_gb', 0)} GB ({health_info.get('percent_free', 0)}%)")
                print(f"  Health:     {health_info.get('status')}")
                print("\nTip: Run 'demo_app --help' to explore subcommands and options.")
                print("=" * 60)
                return 0

        # Execute requested components
        greeting_result: Optional[str] = None
        calculation_result: Optional[Dict[str, Any]] = None
        results_combined: Dict[str, Any] = {}
        # Determine semantic command name
        if subcmd:
            command_name = subcmd
        elif name is not None:
            command_name = "greet"
        elif calc_str is not None or op is not None or fib_n is not None or prime_n is not None:
            command_name = "calc"
        elif system_flag or health_flag:
            command_name = "status"
        else:
            command_name = "exec"

        # If calc subcommand is invoked without specific mode, provide sample calculation
        if subcmd == "calc" and calc_str is None and op is None and fib_n is None and prime_n is None:
            calc_str = "1, 2, 3, 4, 5"

        # 1. Greeting computation
        if name is not None or subcmd == "greet" or style != "standard" or template is not None:
            greeting_result = generate_greeting(name=name, style=style, template=template)
            results_combined["greeting"] = greeting_result
            results_combined["target"] = name if name else "World"
            results_combined["style"] = style
            if template:
                results_combined["template"] = template

        # 2. Number list statistics computation
        if calc_str is not None:
            numbers = parse_number_list(calc_str)
            calculation_result = compute_stats(numbers)
            results_combined["calculation"] = calculation_result
            results_combined["stats"] = calculation_result

        # 3. Arithmetic operations
        if op is not None:
            if not op_args or len(op_args) != 2:
                sys.stderr.write("Error: Arithmetic operation --op requires --args A B with exactly two numbers.\n")
                return 1
            arith_val = execute_arithmetic(op, op_args[0], op_args[1])
            arith_dict = {
                "operation": op,
                "operands": op_args,
                "result": arith_val,
            }
            results_combined["arithmetic"] = arith_dict
            if calculation_result is None:
                calculation_result = arith_dict

        # 4. Fibonacci sequence
        if fib_n is not None:
            fib_seq = generate_fibonacci(fib_n)
            fib_dict = {"n": fib_n, "sequence": fib_seq}
            results_combined["fibonacci"] = fib_dict
            if calculation_result is None:
                calculation_result = fib_dict

        # 5. Primality test
        if prime_n is not None:
            prime_dict = check_prime(prime_n)
            results_combined["primality"] = prime_dict
            if calculation_result is None:
                calculation_result = prime_dict

        # 6. System & Workspace health queries
        if system_flag or (subcmd == "status" and not health_flag):
            sys_telemetry = get_system_info()
            results_combined["system"] = sys_telemetry

        if health_flag:
            health_telemetry = get_workspace_health(target_path)
            results_combined["workspace_health"] = health_telemetry

        # Emit output
        if is_json:
            print(
                format_json_envelope(
                    command=command_name,
                    result=results_combined,
                    greeting=greeting_result,
                    calculation=calculation_result,
                )
            )
            return 0

        # Human-readable stdout output
        if greeting_result:
            print(greeting_result)

        if calculation_result and "count" in calculation_result:
            print("Calculation Results:")
            print(f"  Count:    {calculation_result['count']}")
            print(f"  Sum:      {calculation_result['sum']}")
            print(f"  Mean:     {calculation_result['mean']}")
            print(f"  Median:   {calculation_result['median']}")
            print(f"  Min:      {calculation_result['min']}")
            print(f"  Max:      {calculation_result['max']}")
            print(f"  Std Dev:  {calculation_result['std_dev']}")

        if "arithmetic" in results_combined:
            ad = results_combined["arithmetic"]
            print(f"Result: {ad['operands'][0]} {ad['operation']} {ad['operands'][1]} = {ad['result']}")

        if "fibonacci" in results_combined:
            fd = results_combined["fibonacci"]
            print(f"Fibonacci ({fd['n']}): {fd['sequence']}")

        if "primality" in results_combined:
            pd = results_combined["primality"]
            status_str = "prime" if pd["is_prime"] else "composite"
            print(f"{pd['n']} is {status_str}. Factors: {pd['factors']}")

        if "system" in results_combined:
            sd = results_combined["system"]
            print("System Diagnostics:")
            for k, v in sd.items():
                print(f"  {k}: {v}")

        if "workspace_health" in results_combined:
            wh = results_combined["workspace_health"]
            print(f"Workspace Health: {wh.get('status')}")
            print(f"  Path:         {wh.get('path')}")
            print(f"  Free Space:   {wh.get('free_gb')} GB ({wh.get('percent_free')}%)")
            print(f"  Total Space:  {wh.get('total_gb')} GB")

        return 0

    except ZeroDivisionError as zde:
        sys.stderr.write(f"Error: {zde}\n")
        return 1
    except ValueError as ve:
        err_msg = str(ve)
        if "Invalid numeric value" in err_msg:
            # Extract token if available
            token = err_msg.split("'")[1] if "'" in err_msg else ""
            sys.stderr.write(f"Error: Invalid numeric value '{token}' in --calc argument\n")
        else:
            sys.stderr.write(f"Error: {err_msg}\n")
        return 1
    except Exception as exc:  # pragma: no cover
        sys.stderr.write(f"Error: {exc}\n")
        return 1
