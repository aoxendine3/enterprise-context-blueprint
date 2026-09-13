"""Executable package module entrypoint for demo_app.

Allows running demo_app via: python -m demo_app [args]
"""

import sys
from demo_app.cli import main

if __name__ == "__main__":
    sys.exit(main())
