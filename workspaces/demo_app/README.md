# SSOT Demonstration Application (`demo_app`)

A high-integrity demonstration application engineered for the **SSOT Agentic Brain** workspace. Built in accordance with AGENTS.md guardrails and workspace architectural principles.

## Overview

- **Zero External Dependencies**: Implemented purely using the Python 3 Standard Library (`argparse`, `json`, `math`, `statistics`, `platform`, `sys`, `os`, `shutil`, `unittest`).
- **Sovereign & Local-First**: Operates 100% offline on bare metal with zero cloud token consumption.
- **Dual Execution Models**:
  - Direct root script execution: `python main.py [options]`
  - Standard package module execution: `python -m demo_app [options]`
- **Rigorous Exit Code Contracts**:
  - `0`: Success
  - `1`: Operational / domain error (e.g. division by zero, malformed calculation inputs)
  - `2`: CLI argument syntax or validation error (e.g. unrecognized flag, missing argument)
- **Universal Structured JSON Support**: Pass `--json` to any command for strictly valid JSON on `stdout`.

---

## Directory Structure

```
workspaces/demo_app/
├── README.md                      # Documentation, usage guide, and verification
├── main.py                        # Root execution entrypoint
├── demo_app/                      # Core application package
│   ├── __init__.py                # Package version marker (__version__ = "1.0.0")
│   ├── __main__.py                # Executable module entrypoint
│   ├── cli.py                     # Argument parser, dispatcher, JSON engine, exit codes
│   ├── greeting.py                # Greeting generator, tone styles, template interpolation
│   └── processor.py               # Diagnostics, health checks, arithmetic, statistics, algorithms
└── tests/                         # Comprehensive test harness
    ├── __init__.py
    ├── run_tests.py               # Standalone test runner and summary reporter
    ├── test_greeting.py           # Unit tests for greeting engine (T-UNIT-01..09)
    ├── test_processor.py          # Unit tests for processor and math (T-UNIT-10..17)
    ├── test_cli.py                # Unit tests for CLI parsing and dispatch (T-UNIT-18..22)
    └── test_integration.py        # Subprocess E2E CLI tests (T-E2E-01..17)
```

---

## Command Line Usage

### 1. Default Demonstration Mode
Running without arguments showcases the default greeting and system health status overview:
```bash
python main.py
```

### 2. Greeting Engine
Generate default, named, or styled greetings:
```bash
# Default greeting ("Hello, World!")
python main.py greet

# Custom recipient
python main.py --name "Anthony"

# Tone styles: standard, formal, casual, sovereign, enthusiastic
python main.py --name "Anthony" --style formal
python main.py --name "Anthony" --style sovereign
python main.py --name "Anthony" --style casual
python main.py --name "Anthony" --style enthusiastic

# Safe template interpolation ({name}, {date}, {time})
python main.py --template "Welcome aboard, {name}! Session started at {time}." --name "Anthony"
```

### 3. System Diagnostics & Workspace Health
Inspect host telemetry and storage metrics:
```bash
# System environment details
python main.py status --system

# Workspace accessibility and disk metrics
python main.py status --health
```

### 4. Mathematical & Algorithmic Computations
Execute statistical summarization, arithmetic, Fibonacci sequences, and primality tests:
```bash
# Statistical summary (count, sum, mean, median, min, max, stdev)
python main.py --calc "10, 20, 30, 40, 50"

# Arithmetic operations with zero-safety (add, sub, mul, div, pow, mod)
python main.py calc --op add --args 15 25
python main.py calc --op div --args 100 4

# Division by zero protection (exits with code 1)
python main.py calc --op div --args 100 0

# Fibonacci sequence generation
python main.py calc --fib 10

# Primality verification and factorization
python main.py calc --prime 29
python main.py calc --prime 30
```

### 5. Structured JSON Output (`--json`)
Append `--json` to any command for machine-readable output:
```bash
python main.py --name "Anthony" --style sovereign --json
python main.py --calc "10, 20, 30, 40" --json
python main.py status --system --json
```

---

## Verification & Testing

### Run All Tests via Standalone Runner
```bash
python workspaces/demo_app/tests/run_tests.py
```

### Run via Standard Library `unittest` Discovery
```bash
python -m unittest discover -s workspaces/demo_app/tests -v
```

All unit and integration tests are self-contained and run 100% offline without third-party dependencies.
