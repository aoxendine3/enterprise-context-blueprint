#!/usr/bin/env python3
"""
FULL HOME CENSUS — measurable, evidence-based inventory of /Users/ajoxendine68.
No secret values are read or stored. Coverage is counted per domain so the
"100% knowing the full depth" bar is MEASURABLE, not asserted.

Writes memory/catch_log/FULL_HOME_CENSUS.json
"""
import os, json, time, subprocess
from pathlib import Path

HOME = Path("/Users/ajoxendine68")
SSOT = HOME / "Desktop/SSOT_Agentic_Brain"
OUT = SSOT / "memory/catch_log/FULL_HOME_CENSUS.json"

# Domains: (label, path, inspect_depth). None = user home root.
DOMAINS = [
    ("home_dotfiles", HOME, 1),
    ("ssot_root", SSOT, 1),
    ("ssot_core", SSOT / "core", 2),
    ("ssot_ops", SSOT / "ops", 2),
    ("ssot_memory", SSOT / "memory", 2),
    ("ssot_docs", SSOT / "docs", 2),
    ("ssot_workspaces", SSOT / "workspaces", 2),
    ("ssot_labs", SSOT / "labs", 2),
    ("ssot_barn", SSOT / "barn", 2),
    ("ssot_scratch", SSOT / "scratch", 2),
    ("ssot_archives", SSOT / "archives", 2),
    ("ssot_artifacts", SSOT / "artifacts", 2),
    ("ssot_code", SSOT / "code", 2),
    ("ssot_identity", SSOT / "identity", 2),
    ("ssot_cards", SSOT / "Xoras_agent_cards", 2),
    ("ssot_governance", SSOT / "core/governance", 2),
    ("home_config", HOME / ".config", 3),
    ("home_sovereign", HOME / ".sovereign", 3),
    ("home_sovereign_witness", HOME / ".sovereign_witness", 3),
    ("home_gemini_brains", HOME / ".gemini/antigravity/brain", 2),
    ("home_agents", HOME / ".agents", 3),
    ("home_claude", HOME / ".claude", 3),
    ("home_codex", HOME / ".codex", 3),
    ("home_ollama", HOME / ".ollama", 3),
    ("home_ssh", HOME / ".ssh", 2),
    ("home_fly_kube", HOME / ".kube", 3),
]

SKIP_PARTS = {"node_modules", "__pycache__", ".git", "target", "Caches",
              ".Trash", "site-packages", ".next", "venv", ".venv"}


def census_dir(path, depth):
    """List first `depth` levels with type/size — no content, no secrets."""
    if not path.exists():
        return {"present": False, "entries": 0, "sample": []}
    entries = []
    def walk(p, lvl):
        try:
            items = sorted(p.iterdir(), key=lambda x: x.name)
        except Exception:
            return
        for it in items:
            if it.name in SKIP_PARTS or it.name.startswith(".") and lvl > 0:
                # still count hidden at level 1 for home; skip deep hidden
                if lvl > 0:
                    continue
            try:
                st = it.lstat()
                rec = {"name": it.name,
                       "type": "link" if it.is_symlink() else ("dir" if it.is_dir() else "file"),
                       "size": st.st_size if it.is_file() else None}
                if it.is_symlink():
                    rec["target"] = str(os.readlink(it))[:120]
                entries.append(rec)
            except Exception:
                pass
            if it.is_dir() and lvl < depth:
                walk(it, lvl + 1)
    walk(path, 0)
    return {"present": True, "entries": len(entries), "sample": entries[:40]}


def file_inventory(path, exts, max_files=400):
    if not path.exists():
        return []
    out = []
    for p in path.rglob("*"):
        if not p.is_file() or p.suffix not in exts:
            continue
        if any(x in p.parts for x in SKIP_PARTS):
            continue
        try:
            out.append({"path": str(p), "bytes": p.stat().st_size})
        except Exception:
            pass
        if len(out) >= max_files:
            break
    return out


result = {}
for label, path, depth in DOMAINS:
    result[label] = {
        "path": str(path),
        "census": census_dir(path, depth),
    }

# Journal / registry / ledger inventory across both memory trees
journals = []
for base in [SSOT / "memory", SSOT / "core/memory", HOME / ".sovereign"]:
    if not base.exists():
        continue
    for p in base.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix in (".jsonl", ".log") or "ledger" in p.name.lower() or "journal" in p.name.lower():
            if any(x in p.parts for x in SKIP_PARTS):
                continue
            try:
                lines = sum(1 for _ in p.open(errors="ignore"))
            except Exception:
                lines = -1
            journals.append({"path": str(p.relative_to(HOME)), "bytes": p.stat().st_size, "lines": lines})
result["journals_and_ledgers"] = sorted(journals, key=lambda x: -x["bytes"])[:60]

# Processes, cron, launch agents (current state)
def sh(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30).stdout.strip()[:4000]
    except Exception:
        return ""
result["runtime"] = {
    "date": sh("date -u +%Y-%m-%dT%H:%M:%SZ"),
    "processes_sonic": sh("ps aux | grep -iE 'sentinel|ollama|daemon|cron|node|python' | grep -v grep | head -25"),
    "crontab": sh("crontab -l 2>/dev/null | head -30"),
    "launch_agents": sh("ls ~/Library/LaunchAgents 2>/dev/null | head -30"),
    "git_head": sh("cd " + str(SSOT) + " && git rev-parse --short HEAD"),
    "git_dirty": sh("cd " + str(SSOT) + " && git status --porcelain | wc -l"),
}

payload = {
    "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "verdict": "FULL_HOME_CENSUS_COMPLETE",
    "domains_inventoried": len(DOMAINS),
    "note": "Metadata only; no secret values read. Coverage is per-domain counts, not a lie of 100% comprehension.",
    "domains": result,
}
OUT.write_text(json.dumps(payload, indent=2))
print(json.dumps({
    "verdict": payload["verdict"],
    "domains": len(DOMAINS),
    "journal_files": len(journals),
    "receipt": str(OUT),
}, indent=2))
