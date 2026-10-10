import time
import subprocess
import urllib.parse
import os

LAST_REPLY_FILE = os.path.expanduser('~/monitor_last_reply.txt')
REPLY_TEMPLATE = "We acknowledge the latest input and will incorporate it into the ongoing synthesis."

def get_last_stored_reply():
    if os.path.exists(LAST_REPLY_FILE):
        with open(LAST_REPLY_FILE, 'r') as f:
            return f.read().strip()
    return ''

def store_last_reply(reply_id):
    with open(LAST_REPLY_FILE, 'w') as f:
        f.write(reply_id)

def check_chrome_notifications():
    script = '''
    tell application "Google Chrome"
        set foundTab to false
        repeat with w in windows
            repeat with t in tabs of w
                if URL of t contains "x.com/notifications" or URL of t contains "x.com/grok/status" then
                    set active tab of w to t
                    set foundTab to true
                    return URL of t
                end if
            end repeat
        end repeat
        return "NOT_FOUND"
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return result.stdout.strip()

def fetch_latest_reply_id(thread_url):
    # Simple heuristic: the URL contains the tweet ID of the latest reply after a '/'
    # Example: https://x.com/user/status/1234567890123456789
    parts = thread_url.rstrip('/').split('/')
    if parts and parts[-1].isdigit():
        return parts[-1]
    return ''

def post_reply(thread_url, reply_text):
    # AppleScript to focus tab, click reply, type text, and submit
    script = f'''
    tell application "Google Chrome"
        repeat with w in windows
            repeat with t in tabs of w
                if URL of t contains "{thread_url}" then
                    set active tab of w to t
                    set frontmost of application "Google Chrome" to true
                    delay 0.5
                    -- Open reply box via keyboard shortcut Cmd+Shift+R (common for X)
                    tell application "System Events"
                        keystroke "r" using {{command down, shift down}}
                        delay 0.5
                        keystroke "{reply_text}"
                        delay 0.2
                        keystroke return
                    end tell
                    exit repeat
                end if
            end repeat
        end repeat
    end tell
    '''
    subprocess.run(["osascript", "-e", script])

def main():
    print("[MONITOR] Starting active background monitor for X replies...")
    last_reply_id = get_last_stored_reply()
    while True:
        active_url = check_chrome_notifications()
        if active_url != "NOT_FOUND":
            reply_id = fetch_latest_reply_id(active_url)
            if reply_id and reply_id != last_reply_id:
                print(f"[MONITOR] New reply detected: {reply_id}")
                post_reply(active_url, REPLY_TEMPLATE)
                store_last_reply(reply_id)
                last_reply_id = reply_id
        time.sleep(30)

if __name__ == "__main__":
    main()
