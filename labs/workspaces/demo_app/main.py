#!/usr/bin/env python3
"""Root execution entrypoint for SSOT Demonstration Application (demo_app).

Usage:
    python main.py [options] [subcommand]
"""

import os
import sys

# Ensure local package directory is on PYTHONPATH
_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from demo_app.cli import main

if __name__ == "__main__":
    sys.exit(main())
