#!/usr/bin/env python3
import subprocess
import time
import os

def set_clipboard(text):
    p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
    p.communicate(input=text.encode("utf-8"))

def paste_separated():
    title = "Multi-Turn Agentic Context Decay & State Pollution: Benchmarking 18,432-D Poincaré Memory vs Gemini 3.5 & Gemma-4"
    tags = "devchallenge, kagglechallenge, ai, machinelearning"
    
    post_path = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/docs/plans/DEV_KAGGLE_BENCHMARK_POST_READY.md"
    with open(post_path, "r", encoding="utf-8") as f:
        full_text = f.read()
        
    # Strip frontmatter from body text so body textarea gets pure markdown
    if full_text.startswith("---"):
        parts = full_text.split("---", 2)
        if len(parts) >= 3:
            body = parts[2].strip()
        else:
            body = full_text
    else:
        body = full_text
        
    print("1. Launching clean DEV.to editor...")
    subprocess.run(["open", "https://dev.to/new"])
    time.sleep(2.5) # Wait for page and title input focus to render
    
    print("2. Pasting Title into Title Field...")
    set_clipboard(title)
    applescript_title = """
    tell application "Google Chrome" to activate
    delay 0.3
    tell application "System Events"
        tell process "Google Chrome"
            -- Select all in Title field & paste title
            keystroke "a" using {command down}
            delay 0.1
            keystroke "v" using {command down}
            delay 0.3
            -- Tab to Tags field
            key code 48
            delay 0.3
        end tell
    end tell
    """
    subprocess.run(["osascript", "-e", applescript_title])
    
    print("3. Pasting Tags into Tags Field...")
    set_clipboard(tags)
    applescript_tags = """
    tell application "System Events"
        tell process "Google Chrome"
            keystroke "a" using {command down}
            delay 0.1
            keystroke "v" using {command down}
            delay 0.3
            -- Tab to Body Textarea
            key code 48
            delay 0.3
        end tell
    end tell
    """
    subprocess.run(["osascript", "-e", applescript_tags])
    
    print("4. Pasting Body Markdown into Main Body Area...")
    set_clipboard(body)
    applescript_body = """
    tell application "System Events"
        tell process "Google Chrome"
            keystroke "a" using {command down}
            delay 0.1
            keystroke "v" using {command down}
            delay 0.5
        end tell
    end tell
    """
    subprocess.run(["osascript", "-e", applescript_body])
    print("Successfully populated Title, Tags, and Body into distinct DEV.to editor inputs!")

if __name__ == "__main__":
    paste_separated()
