import time
import subprocess
import sqlite3
import os
import urllib.request
import json
from datetime import datetime

DB_PATH = "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/Source/sentinel.db"
LOG_OUT = "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/Omni_Dojo_Sandbox/xoras_daemon.out"

# Elite enterprise-grade repositories to hunt for targets
TARGET_REPOS = [
    "kubernetes/kubernetes",
    "facebook/react",
    "tensorflow/tensorflow"
]


def log(msg):
    with open(LOG_OUT, "a") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")


def notify_anthony(title, message):
    """Sends a native macOS desktop notification."""
    script = f'display notification "{message}" with title "{title}"'
    subprocess.run(["osascript", "-e", script])


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS autonomous_tasks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  task_type TEXT, 
                  status TEXT, 
                  payload TEXT, 
                  source_url TEXT,
                  created_at TEXT)''')
    conn.commit()
    conn.close()


def fetch_impossible_problems():
    """Polls elite enterprise repos for critical issues."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    new_tasks = 0
    for repo in TARGET_REPOS:
        # Search for open issues labeled 'bug' with high discussion volume
        url = f"https://api.github.com/search/issues?q=repo:{repo}+type:issue+state:open+label:bug+sort:comments-desc&per_page=3"
        try:
            req = urllib.request.Request(
                url, headers={'User-Agent': 'Xoras-Sovereign-Daemon'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())

                for item in data.get('items', []):
                    issue_url = item['html_url']
                    title = item['title']

                    # Check if already in db
                    c.execute(
                        "SELECT id FROM autonomous_tasks WHERE source_url=?", (issue_url,))
                    if not c.fetchone():
                        # Insert new task
                        payload = json.dumps(
                            {"title": title, "body": item.get('body', '')[:500]})
                        c.execute("INSERT INTO autonomous_tasks (task_type, status, payload, source_url, created_at) VALUES (?, ?, ?, ?, ?)",
                                  ('BOUNTY_HUNTER', 'PENDING_ANALYSIS', payload, issue_url, datetime.now().isoformat()))
                        new_tasks += 1
                        log(f"Acquired new target: {title} from {repo}")
        except Exception as e:
            log(f"Error fetching from {repo}: {e}")

    conn.commit()
    conn.close()
    return new_tasks


def daemon_loop():
    log("Daemon initializing Bounty Hunter Protocol...")
    init_db()
    notify_anthony("Xoras Daemon: Bounty Hunter Live",
                   "Wired into global feeds. Scanning enterprise repos for targets.")
    log("Bounty Hunter module active. Scanning...")

    while True:
        try:
            new_targets = fetch_impossible_problems()
            if new_targets > 0:
                notify_anthony(
                    "Xoras: Target Acquired", f"Pulled {new_targets} new impossible problems into the local database for analysis.")

            # Sleep for 15 minutes to respect API rate limits and stay under the radar
            time.sleep(900)

        except Exception as e:
            log(f"Daemon encountered a fault: {str(e)}")
            time.sleep(60)


if __name__ == "__main__":
    daemon_loop()
