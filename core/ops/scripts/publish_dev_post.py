#!/usr/bin/env python3
import subprocess
import time

def publish_post():
    # AppleScript to target Chrome/default browser and click Publish / press submit
    script = """
    tell application "Google Chrome"
        activate
        delay 1
        tell active tab of front window
            execute javascript "
                // Find and click publish button on DEV.to editor
                const btns = Array.from(document.querySelectorAll('button, input[type=submit]'));
                const publishBtn = btns.find(b => b.textContent.strip?.().toLowerCase().includes('publish') || b.textContent.toLowerCase().includes('submit') || b.value?.toLowerCase().includes('publish'));
                if (publishBtn) {
                    publishBtn.click();
                    'CLICKED_PUBLISH_BUTTON';
                } else {
                    // Fallback to form submit
                    const form = document.querySelector('form');
                    if (form) { form.submit(); 'SUBMITTED_FORM'; }
                    else { 'BUTTON_NOT_FOUND'; }
                }
            "
        end tell
    end tell
    """
    
    try:
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        print("AppleScript execution result:", res.stdout.strip(), res.stderr.strip())
    except Exception as e:
        print("AppleScript error:", e)

    # Secondary fallback: send shortcut Cmd+Enter via System Events
    shortcut_script = """
    tell application "System Events"
        tell process "Google Chrome"
            set frontmost to true
            delay 0.5
            keystroke return using {command down}
        end tell
    end tell
    """
    try:
        res2 = subprocess.run(["osascript", "-e", shortcut_script], capture_output=True, text=True)
        print("Shortcut execution result:", res2.stdout.strip(), res2.stderr.strip())
    except Exception as e:
        print("Shortcut error:", e)

if __name__ == "__main__":
    publish_post()
