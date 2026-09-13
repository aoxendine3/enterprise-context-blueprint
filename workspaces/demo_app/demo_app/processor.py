"""Processor module for SSOT Demonstration Application.

Provides system diagnostics, workspace health checks, arithmetic operations,
statistical computations, Fibonacci generation, and primality verification.
Zero external dependencies.
"""

from __future__ import annotations

import datetime
import math
import os
import platform
import shutil
import statistics
from typing import Any, Dict, List, Optional

from demo_app import __app_name__, __version__


def get_system_info() -> Dict[str, Any]:
    """Gather non-invasive, read-only system and platform information.

    Returns:
        Dictionary containing OS, platform, python version, working directory,
        host node name, and UTC timestamp.
    """
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    return {
        "os": platform.system(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cwd": os.getcwd(),
        "node": platform.node(),
        "timestamp": now_utc.isoformat(),
    }


def get_workspace_health(workspace_path: Optional[str] = None) -> Dict[str, Any]:
    """Inspect workspace accessibility and storage health.

    Args:
        workspace_path: Path to workspace. Defaults to current working directory.

    Returns:
        Dictionary containing health status, accessibility flag, and disk metrics.
    """
    target_path = workspace_path if workspace_path is not None else os.getcwd()
    accessible = os.path.exists(target_path) and os.access(target_path, os.R_OK)

    if not accessible:
        return {
            "status": "UNHEALTHY",
            "accessible": False,
            "path": target_path,
            "error": f"Path '{target_path}' does not exist or is not readable.",
        }

    try:
        usage = shutil.disk_usage(target_path)
        total_gb = round(usage.total / (1024**3), 2)
        used_gb = round(usage.used / (1024**3), 2)
        free_gb = round(usage.free / (1024**3), 2)
        percent_free = round((usage.free / usage.total) * 100, 2) if usage.total > 0 else 0.0

        status = "HEALTHY" if percent_free > 1.0 else "WARNING_LOW_DISK"
        return {
            "status": status,
            "accessible": True,
            "path": target_path,
            "total_bytes": usage.total,
            "used_bytes": usage.used,
            "free_bytes": usage.free,
            "total_gb": total_gb,
            "used_gb": used_gb,
            "free_gb": free_gb,
            "percent_free": percent_free,
        }
    except Exception as exc:  # pragma: no cover
        return {
            "status": "DEGRADED",
            "accessible": True,
            "path": target_path,
            "error": str(exc),
        }


def get_system_status() -> Dict[str, Any]:
    """Return application-level status and metadata."""
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    return {
        "status": "OK",
        "app_name": __app_name__,
        "version": __version__,
        "timestamp": now_utc.isoformat(),
    }


def parse_number_list(numbers_str: str) -> List[float]:
    """Parse a delimited string of numbers into a list of floats.

    Args:
        numbers_str: Comma or whitespace separated numbers (e.g. '1, 2, 3, 4.5').

    Returns:
        List of parsed floats.

    Raises:
        ValueError: If input is empty or contains non-numeric tokens.
    """
    if not isinstance(numbers_str, str) or numbers_str.strip() == "":
        raise ValueError("Cannot parse empty number list")

    # Replace commas with spaces and split on whitespace
    normalized = numbers_str.replace(",", " ")
    tokens = normalized.split()

    if not tokens:
        raise ValueError("Cannot parse empty number list")

    parsed: List[float] = []
    for token in tokens:
        try:
            parsed.append(float(token))
        except ValueError:
            raise ValueError(f"Invalid numeric value '{token}' in number list")

    return parsed


def compute_stats(numbers: List[float]) -> Dict[str, Any]:
    """Compute aggregate statistical metrics for a numeric sequence.

    Args:
        numbers: List of floats or ints. Must not be empty.

    Returns:
        Dictionary with count, sum, mean, median, min, max, variance, std_dev.

    Raises:
        ValueError: If numbers list is empty.
    """
    if not numbers:
        raise ValueError("Cannot compute statistics on empty data")

    count = len(numbers)
    total_sum = float(sum(numbers))
    mean_val = float(statistics.mean(numbers))
    median_val = float(statistics.median(numbers))
    min_val = float(min(numbers))
    max_val = float(max(numbers))

    if count > 1:
        variance_val = float(statistics.variance(numbers))
        stdev_val = float(statistics.stdev(numbers))
    else:
        variance_val = 0.0
        stdev_val = 0.0

    return {
        "count": count,
        "sum": total_sum,
        "mean": mean_val,
        "median": median_val,
        "min": min_val,
        "max": max_val,
        "variance": variance_val,
        "std_dev": stdev_val,
    }


def execute_arithmetic(op: str, a: float, b: float) -> float:
    """Execute standard arithmetic operation with zero-division safety.

    Args:
        op: Operation ('add', 'sub', 'mul', 'div', 'pow', 'mod').
        a: First operand.
        b: Second operand.

    Returns:
        Numeric result of the operation.

    Raises:
        ZeroDivisionError: If attempting to divide or modulo by zero.
        ValueError: If operation is not supported.
    """
    normalized_op = op.lower().strip() if isinstance(op, str) else ""

    if normalized_op == "add":
        return a + b
    elif normalized_op == "sub":
        return a - b
    elif normalized_op == "mul":
        return a * b
    elif normalized_op == "div":
        if b == 0:
            raise ZeroDivisionError("Division by zero is undefined")
        return a / b
    elif normalized_op == "pow":
        return a ** b
    elif normalized_op == "mod":
        if b == 0:
            raise ZeroDivisionError("Modulo by zero is undefined")
        return a % b
    else:
        valid_ops = "add, sub, mul, div, pow, mod"
        raise ValueError(f"Unknown operation '{op}'. Supported operations are: {valid_ops}")


def generate_fibonacci(n: int) -> List[int]:
    """Generate the first N numbers of the Fibonacci sequence.

    Args:
        n: Number of elements to generate (1 <= n <= 1000).

    Returns:
        List of first n Fibonacci numbers (0-indexed: [0, 1, 1, 2, ...]).

    Raises:
        ValueError: If n is not within [1, 1000].
    """
    if not isinstance(n, int) or n < 1 or n > 1000:
        raise ValueError(f"n must be an integer between 1 and 1000, got {n}")

    if n == 1:
        return [0]
    if n == 2:
        return [0, 1]

    seq = [0, 1]
    for _ in range(2, n):
        seq.append(seq[-1] + seq[-2])
    return seq


def check_prime(n: int) -> Dict[str, Any]:
    """Test primality and compute factors for a positive integer.

    Args:
        n: Positive integer >= 1.

    Returns:
        Dictionary containing n, is_prime boolean, and list of all factors.

    Raises:
        ValueError: If n < 1.
    """
    if not isinstance(n, int) or n < 1:
        raise ValueError(f"n must be a positive integer >= 1, got {n}")

    factors: List[int] = []
    # Find all factors
    for i in range(1, int(math.isqrt(n)) + 1):
        if n % i == 0:
            factors.append(i)
            counterpart = n // i
            if counterpart != i:
                factors.append(counterpart)

    factors.sort()
    is_prime = (n > 1) and (len(factors) == 2)

    return {
        "n": n,
        "is_prime": is_prime,
        "factors": factors,
    }
