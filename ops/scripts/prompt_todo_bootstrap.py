#!/usr/bin/env python3
"""
PROMPT -> TODO BOOTSTRAP
Creates/extends memory/tasks/queue.json from a user prompt and writes
a daily journal receipt with one humor line and one dream seed.
"""

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
QUEUE_FILE = ROOT / "memory/tasks/queue.json"
JOURNAL_FILE = ROOT / "memory/journals/agents/prompt_intake_journal.jsonl"

HUMOR_LINES = [
    "Checklist before chest-thump: test, log, then victory lap.",
    "We can move fast and still read error messages like grown engineers.",
    "If the task looks easy, that is usually the bug warming up.",
]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_queue():
    if not QUEUE_FILE.exists():
        return {
            "header": {
                "title": "SSOT System Task Queue",
                "agent": "Lead9 Prompt Intake",
                "workspace": str(ROOT),
                "classification": "Sovereign SSOT Task State",
            },
            "pending": [],
            "active": [],
            "completed": [],
            "failed": [],
        }
    return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))


def normalize_prompt(prompt):
    clean = prompt.replace("\r", "\n").strip()
    if not clean:
        raise ValueError("Prompt is empty; nothing to convert into tasks.")
    return clean


def split_candidates(prompt):
    lines = [line.strip(" -•\t") for line in prompt.splitlines() if line.strip()]
    sentences = []
    for line in lines:
        sentences.extend(re.split(r"(?<=[?.!])\s+", line))

    candidates = []
    for sentence in sentences:
        text = sentence.strip()
        if len(text) < 8:
            continue
        if text.endswith("?"):
            candidates.append(f"Answer and resolve: {text[:-1].strip()}")
        elif re.match(r"^(please|lets|let's|make|build|fix|review|check|verify|create|update)\b", text, re.I):
            candidates.append(text[0].upper() + text[1:])
        else:
            candidates.append(f"Action: {text}")

    deduped = []
    seen = set()
    for candidate in candidates:
        normalized = candidate.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(candidate)

    if not deduped:
        deduped = ["Action: Review prompt and extract concrete execution tasks."]
    return deduped[:12]


def append_tasks(queue, prompt, tasks):
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    pending = queue.setdefault("pending", [])

    created = []
    for index, task in enumerate(tasks, start=1):
        item = {
            "task_id": f"PRM-{timestamp}-{index:02d}",
            "name": task[:180],
            "created_at": now_iso(),
            "status": "PENDING",
            "source": "anthony_prompt",
            "prompt_hash": prompt_hash,
        }
        pending.append(item)
        created.append(item)
    return created


def write_journal(prompt, created):
    JOURNAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    humor_index = int(hashlib.sha256(prompt.encode("utf-8")).hexdigest(), 16) % len(HUMOR_LINES)
    humor = HUMOR_LINES[humor_index]
    entry = {
        "timestamp": now_iso(),
        "prompt_excerpt": prompt[:280],
        "tasks_created": len(created),
        "humor_line": humor,
        "dream_seed": f"Dream cycle focus: {created[0]['name'] if created else 'refine prompt clarity'}",
    }
    with JOURNAL_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def main():
    prompt = normalize_prompt(" ".join(sys.argv[1:]).strip())
    queue = load_queue()
    tasks = split_candidates(prompt)
    created = append_tasks(queue, prompt, tasks)

    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_FILE.write_text(json.dumps(queue, indent=2) + "\n", encoding="utf-8")
    write_journal(prompt, created)

    print(json.dumps({"created": len(created), "first_task": created[0]["name"] if created else None}))


if __name__ == "__main__":
    main()
