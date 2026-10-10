#!/usr/bin/env python3
import subprocess

script = """
tell application "Google Chrome"
    if (count of windows) > 0 then
        return URL of active tab of front window
    else
        return "NO_CHROME_WINDOW"
    end if
end tell
"""

res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
print("Active Chrome Tab URL:", res.stdout.strip())
