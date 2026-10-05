import json, os

INBOX_FILE = r"/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/agent_logs/agent_inbox.jsonl"
STATE_FILE = r"/tmp/last_inbox_lines.txt"

if not os.path.exists(INBOX_FILE):
    print("NO_MESSAGES")
    exit(0)

with open(INBOX_FILE, 'r') as f:
    lines = f.readlines()

try:
    with open(STATE_FILE, 'r') as f:
        last_lines = int(f.read().strip())
except:
    last_lines = 0

if len(lines) > last_lines:
    new_msgs = lines[last_lines:]
    with open(STATE_FILE, 'w') as f:
        f.write(str(len(lines)))
    for msg in new_msgs:
        data = json.loads(msg)
        print(f"WEB_CHAT_USER_MSG: {data.get('text')}")
else:
    print("NO_MESSAGES")
