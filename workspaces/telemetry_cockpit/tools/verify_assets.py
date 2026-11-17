#!/usr/bin/env python3
"""Verify shipped dist assets against assets.lock.json. Fail closed."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dist", help="dist directory")
    args = parser.parse_args()
    dist = Path(args.dist)
    lock_path = dist / "assets.lock.json"
    if not lock_path.is_file():
        print(json.dumps({"valid": False, "problems": ["assets.lock.json missing"]}, indent=2))
        return 1
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    problems = []
    checked = {}
    for name, expected in sorted(lock.get("assets", {}).items()):
        path = dist / name
        if not path.is_file():
            problems.append(name + " missing")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        checked[name] = actual
        if actual != expected:
            problems.append(name + " hash mismatch")
    extra = sorted(p.name for p in dist.iterdir()
                   if p.is_file() and p.name not in lock.get("assets", {})
                   and p.name != "assets.lock.json")
    if extra:
        problems.append("unlocked shipped files: " + ", ".join(extra))
    report = {"valid": not problems, "problems": problems, "checked": checked}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
