#!/usr/bin/env python3
"""Read the latest health audit report and speak its contents using the default macOS voice.
The script expects `audit_report.html` to be present in the same directory as this file.
"""
import pathlib, subprocess, sys

REPORT = pathlib.Path(__file__).resolve().parents[2] / ".agents" / "skills" / "health-walkthrough-audit" / "audit_report.html"
if not REPORT.is_file():
    print(f"[ERROR] Report not found at {REPORT}", file=sys.stderr)
    sys.exit(1)

# Extract text from HTML (very simple stripping of tags)
content = REPORT.read_text(encoding="utf-8")
# naive removal of HTML tags for speaking
import re
text = re.sub(r"<[^>]+>", " ", content)
text = re.sub(r"\s+", " ", text).strip()

# Speak using default mac voice
subprocess.run(["say", text])
