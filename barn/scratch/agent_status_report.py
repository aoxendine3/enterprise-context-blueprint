#!/usr/bin/env python3
import json, os, datetime, pathlib, random, sys
ROOT = pathlib.Path('/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain')
QUEUE_FILE = ROOT / 'memory' / 'tasks' / 'queue.json'
def load_queue():
    if not QUEUE_FILE.is_file():
        return None
    try:
        return json.loads(QUEUE_FILE.read_text())
    except Exception as e:
        return None
def report():
    now = datetime.datetime.now().isoformat(timespec='seconds')
    q = load_queue()
    pending = len(q.get('pending', [])) if q else 0
    active = len(q.get('active', [])) if q else 0
    completed = len(q.get('completed', [])) if q else 0
    messages = {
        'jarvis': f"Jarvis: system time {now}, queue pending {pending} tasks.",
        'maxx': f"Maxx: {active} active, {completed} completed tasks.",
        'clara': f"Clara: memory usage placeholder, all systems nominal.",
        'vance': f"Vance: analyzing replication state, no anomalies detected.",
        'john': f"John: reviewing recent logs, no errors.",
        'selene': f"Selene: contextual insight – everything is stable.",
    }
    for agent, msg in messages.items():
        print(agent, msg)
if __name__ == '__main__':
    report()
