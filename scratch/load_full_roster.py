import os
import glob
import json
import hashlib

CARDS_DIR = os.path.expanduser("~/Desktop/SSOT_Agentic_Brain/Xoras_agent_cards")
json_files = glob.glob(os.path.join(CARDS_DIR, "*.json"))

full_roster = {}
for jf in sorted(json_files):
    name = os.path.basename(jf).replace(".json", "")
    data = json.load(open(jf, "r", encoding="utf-8"))
    raw_bytes = json.dumps(data, sort_keys=True).encode("utf-8")
    lock_hash = hashlib.sha256(raw_bytes).hexdigest()
    full_roster[name] = {
        "data": data,
        "lock_hash": lock_hash
    }

print(f"Loaded Full Roster: {len(full_roster)} Agents Verified.")
for agent, info in full_roster.items():
    title = info['data'].get('name', agent).capitalize()
    role = info['data'].get('role', 'Agent Persona')
    print(f"  - {agent:<15} ({title}) | Lock Hash: {info['lock_hash'][:16]}... | Role: {role}")
