# Project: SSOT Demonstration Application (demo_app)

## Architecture
- **Location**: `c:\Users\admin\Desktop\SSOT_Agentic_Brain\workspaces\demo_app` (compliant with AGENTS.md Guardrail 1)
- **Language / Runtime**: Pure Python 3 (Python 3.10+) with ZERO external dependencies. Standard library only (`argparse`, `json`, `math`, `statistics`, `platform`, `sys`, `os`, `pathlib`, `unittest`).
- **Execution Model**:
  - Direct root runner: `python workspaces/demo_app/main.py [args]`
  - Package module execution: `python -m demo_app [args]` (when `workspaces/demo_app` is in PYTHONPATH or CWD)
- **Data Flow & Interface**:
  - `cli.py` parses CLI flags and subcommands (`greet`, `status`, `calc`).
  - `greeting.py` generates default/named greetings, tone styles, and template interpolation.
  - `processor.py` executes system diagnostics, disk/workspace health checks, arithmetic, statistics, and number algorithms.
  - Formatter handles standard text output vs strict machine-readable JSON (`--json`).
  - Standard exit codes: `0` = success, `1` = operational/domain error, `2` = invalid CLI argument.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | F1: CLI Entrypoint & Dispatcher | Root runner (`main.py`) & package dispatcher routing commands or default summary | M1 | survey |
| 2 | F2: Help & Self-Documentation | `--help` / `-h` at top level and per command with usage examples | M1 | survey |
| 3 | F3: Version Reporting | `--version` / `-v` emitting application name and semver string | M1 | survey |
| 4 | F4: Structured Output Engine | `--json` emitting strictly valid JSON to stdout; errors to stderr | M1 | survey |
| 5 | F5: Standard Exit Code Discipline | Exit 0 on success, 1 on domain error, 2 on invalid CLI syntax | M1 | survey |
| 6 | F6: Default & Named Greeting | "Hello, World!" by default or "Hello, <name>!" via `--name` | M1 | survey |
| 7 | F7: Configurable Greeting Styles | Tone styles: standard, formal, casual, sovereign, enthusiastic | M1 | survey |
| 8 | F8: Greeting Template Interpolation | Custom greeting templates supporting `{name}`, `{date}`, `{time}` | M1 | survey |
| 9 | F9: System Environment Diagnostics | Reports OS, platform release, Python version, CWD, host node | M1 | survey |
| 10 | F10: Workspace Health & Storage | Verifies workspace access and reports disk usage and HEALTHY status | M1 | survey |
| 11 | F11: Arithmetic Operations | Basic math (`add`, `sub`, `mul`, `div`, `pow`, `mod`) with zero-division safety | M1 | survey |
| 12 | F12: Statistical Summary Computation | Calculates count, sum, mean, median, min, max, stdev from numeric lists | M1 | survey |
| 13 | F13: Algorithmic Computations | Fibonacci sequence generator and primality testing / factorization | M1 | survey |
| 14 | F14: Test Suite & Runner | Complete unit and integration test suite using standard library `unittest` | M1 | survey |
| 15 | F15: Standalone Test Runner Script | `tests/run_tests.py` providing one-click test execution and summary | M1 | survey |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Core Demonstration Application & Test Suite | Full implementation of demo_app, unit tests, integration tests, and runner | Survey complete | IN_PROGRESS (Phase 2 Verification) |

## Code Layout
```
workspaces/demo_app/
├── main.py                         # Root entrypoint (`python main.py [args]`)
├── README.md                       # Documentation, architecture, and verification commands
├── demo_app/
│   ├── __init__.py                 # Package version (__version__ = "1.0.0")
│   ├── __main__.py                 # Executable module entrypoint
│   ├── cli.py                      # Argument parser, dispatcher, JSON output formatter, exit codes
│   ├── greeting.py                 # Greeting generation, tone styles, template interpolation
│   └── processor.py                # Diagnostics, workspace health, math, statistics, algorithms
└── tests/
    ├── __init__.py
    ├── run_tests.py                # Standalone test runner and summary reporter
    ├── test_greeting.py            # Unit tests for greeting logic (T-UNIT-01..09)
    ├── test_processor.py           # Unit tests for processor/math/diagnostics (T-UNIT-10..17)
    ├── test_cli.py                 # Unit tests for CLI parsing (T-UNIT-18..22)
    └── test_integration.py         # Subprocess E2E CLI tests (T-E2E-01..13)
```

## Interface Contracts
### `greeting.generate_greeting(name=None, style="standard", template=None) -> str`
- Default name: `"World"` if name is None or empty/whitespace.
- Styles: `standard`, `formal`, `casual`, `sovereign`, `enthusiastic`.
- Raises `ValueError` on unknown style.
- Safe template formatting without KeyError.

### `processor.get_system_info() -> dict`
- Keys: `os`, `platform`, `python_version`, `cwd`, `node`, `timestamp`.

### `processor.get_workspace_health(workspace_path=None) -> dict`
- Checks path accessibility, disk metrics (`total_gb`, `used_gb`, `free_gb`, `percent_free`), returns `status: "HEALTHY"`.

### `processor.compute_stats(numbers: list[float]) -> dict`
- Keys: `count`, `sum`, `mean`, `median`, `min`, `max`, `variance`, `std_dev`.
- Raises `ValueError` on empty list.

### `processor.generate_fibonacci(n: int) -> list[int]`
- Returns first n Fibonacci numbers. Raises `ValueError` if n < 1 or n > 1000.

### `processor.check_prime(n: int) -> dict`
- Keys: `n`, `is_prime`, `factors`. Raises `ValueError` if n < 1.

### `cli.main(args=None) -> int`
- Returns exit code: `0` for success, `1` for application error, `2` for invalid arguments.
- Standard JSON envelope when `--json` flag is provided:
  ```json
  {
    "status": "success",
    "timestamp": "ISO8601",
    "result": {},
    "metadata": {
      "app": "demo_app",
      "version": "1.0.0"
    }
  }
  ```
