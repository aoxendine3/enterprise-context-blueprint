#!/usr/bin/env python3
"""Xoras wake entrypoint — loud, human-visible startup sequence.

Usage:
    python3 xoras_wake.py
    python3 xoras_startup.py   # same contract

Prints XORAS WAKE SEQUENCE banners and writes Source/.xoras_wake_status.json.
Exits non-zero on any failed phase (fail-closed health gates).
"""
from __future__ import annotations

import sys

from xoras_startup import run_wake


def main() -> None:
    print("XORAS WAKE SEQUENCE", flush=True)
    sys.exit(run_wake())


if __name__ == "__main__":
    main()
