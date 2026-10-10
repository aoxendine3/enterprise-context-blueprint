#!/usr/bin/env python3
import subprocess
import time
import os

def main():
    post_path = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/docs/plans/DEV_KAGGLE_BENCHMARK_POST_READY.md"
    
    with open(post_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Copy full un-truncated content to macOS system clipboard
    p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
    p.communicate(input=content.encode("utf-8"))
    print(f"Loaded {len(content)} characters of full submission markdown into system clipboard.")
    
    # Open clean DEV.to editor tab
    subprocess.run(["open", "https://dev.to/new"])
    print("Opened https://dev.to/new in default browser.")
    
    # Give browser window 2 seconds to focus and render
    time.sleep(2.0)
    
    # AppleScript GUI automation to click into the main text editor and paste
    applescript_cmd = """
    tell application "System Events"
        delay 0.5
        keystroke "v" using {command down}
    end tell
    """
    
    try:
        subprocess.run(["osascript", "-e", applescript_cmd], check=True)
        print("Successfully dispatched Command+V AppleScript paste event to active browser editor!")
    except Exception as e:
        print(f"AppleScript paste notification: {e}")

    # Write verification log receipt
    log_file = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/catch_log/kaggle_post_automation_receipt.log"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Full article copied to clipboard & browser opened. Length: {len(content)} bytes.\n")
        
if __name__ == "__main__":
    main()
