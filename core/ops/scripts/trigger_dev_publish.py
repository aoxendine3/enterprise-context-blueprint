#!/usr/bin/env python3
import subprocess
import time

def trigger_publish():
    script = """
    tell application "Google Chrome"
        activate
    end tell
    delay 0.8
    tell application "System Events"
        tell process "Google Chrome"
            -- Select all to ensure editor focus, then move to bottom
            keystroke "a" using {command down}
            delay 0.2
            -- Send Command+Enter (DEV.to publish keyboard shortcut)
            keystroke return using {command down}
            delay 1.5
        end tell
    end tell
    """
    res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    print("Publish trigger dispatched via AppleScript:", res.stdout.strip(), res.stderr.strip())

if __name__ == "__main__":
    trigger_publish()
