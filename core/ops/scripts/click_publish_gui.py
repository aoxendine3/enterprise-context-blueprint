#!/usr/bin/env python3
import subprocess
import time

def click_publish_gui():
    applescript = """
    tell application "Google Chrome"
        activate
    end tell
    delay 0.5
    tell application "System Events"
        tell process "Google Chrome"
            -- Press Command+Enter to publish draft on DEV.to
            keystroke return using {command down}
            delay 1.0
            -- Press Tab and Enter as fallback
            key code 48 -- Tab
            delay 0.2
            key code 36 -- Enter
        end tell
    end tell
    """
    res = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True)
    print("GUI Publish Attempt Output:", res.stdout.strip(), res.stderr.strip())

if __name__ == "__main__":
    click_publish_gui()
