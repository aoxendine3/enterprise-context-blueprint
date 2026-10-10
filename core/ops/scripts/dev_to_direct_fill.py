#!/usr/bin/env python3
import subprocess
import time

def fill_dev_editor():
    title = "Multi-Turn Agentic Context Decay & State Pollution: Benchmarking 18,432-D Poincaré Memory vs Gemini 3.5 & Gemma-4"
    tags = "devchallenge, kagglechallenge, ai, machinelearning"
    
    post_path = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/docs/plans/DEV_KAGGLE_BENCHMARK_POST_READY.md"
    with open(post_path, "r", encoding="utf-8") as f:
        full_text = f.read()
        
    if full_text.startswith("---"):
        parts = full_text.split("---", 2)
        body = parts[2].strip() if len(parts) >= 3 else full_text
    else:
        body = full_text

    # Set system clipboard to pure Body Markdown
    p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
    p.communicate(input=body.encode("utf-8"))
    print(f"Loaded Body Markdown ({len(body)} characters) into macOS system clipboard.")

    # AppleScript to focus Chrome and click into body area (approx 400px down from top of window)
    script = """
    tell application "Google Chrome" to activate
    delay 0.5
    tell application "System Events"
        tell process "Google Chrome"
            set win to front window
            set winPosition to position of win
            set winSize to size of win
            
            -- Calculate click point in main body area (center X, 45% Y down)
            set clickX to (item 1 of winPosition) + ((item 1 of winSize) / 2)
            set clickY to (item 2 of winPosition) + ((item 2 of winSize) * 0.45)
            
            click at {clickX, clickY}
            delay 0.3
            keystroke "a" using {command down}
            delay 0.2
            keystroke "v" using {command down}
        end tell
    end tell
    """
    res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    print("Direct Body Click & Paste Result:", res.stdout.strip(), res.stderr.strip())

if __name__ == "__main__":
    fill_dev_editor()
