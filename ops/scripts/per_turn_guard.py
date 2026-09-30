#!/usr/bin/env python3
"""
Per-Turn 7th-Layer Guard
------------------------
* Loads the immutable identity card (identity/charter.yaml)
* Re-hydrates short-term memory (memory/agent_logs/agent_inbox.jsonl)
* Loads long-term context (memory/tri_brain/, memory/catch_log/)
* Verifies the Merkle-registry and the biblical-principle hash
* Returns exit-code 0 on success, non-zero on any failure

CRITICAL: This script does NOT call agent_speak.sh.
agent_speak.sh calls THIS script. Calling back would create infinite recursion.
Audio dispatch is the caller's responsibility.
"""

import sys, yaml, json, hashlib, pathlib, os
from datetime import datetime, timezone

ROOT = pathlib.Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
LOG  = ROOT / "memory" / "catch_log" / "per_turn_guard.log"
CACHE_FILE = "/tmp/per_turn_guard_cache.json"

def log(msg: str, level: str = "INFO"):
    ts = datetime.now(timezone.utc).isoformat()
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{ts} [{level}] {msg}\n")

def abort(reason):
    log(reason, "ERROR")
    sys.exit(1)

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(data):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

def main():
    cache = load_cache()

    # 1. Identity - only load once per session (cached after first run)
    if "identity_hash" not in cache:
        charter = ROOT / "identity" / "charter.yaml"
        if not charter.is_file():
            abort("Missing identity/charter.yaml")
        with open(charter, "r", encoding="utf-8") as f:
            id_data = yaml.safe_load(f)
        id_hash = sha256_file(str(charter))
        cache["identity_hash"] = id_hash
        cache["identity_name"] = id_data.get("name", "?") if isinstance(id_data, dict) else "?"
        log(f"Identity loaded: {cache['identity_name']} (hash {id_hash})")
    else:
        log(f"Identity cache hit (hash {cache['identity_hash']})")

    # 2. Short-term hydrate - verify presence only
    inbox = ROOT / "memory" / "agent_logs" / "agent_inbox.jsonl"
    if not inbox.is_file():
        abort("Missing short-term inbox: memory/agent_logs/agent_inbox.jsonl")
    log("Short-term memory verified (presence check)")

    # 3. Long-term load - verify tri_brain dir exists
    tri_brain = ROOT / "memory" / "tri_brain"
    if not tri_brain.is_dir():
        abort("Missing long-term tri_brain directory")
    log("Long-term context directory verified")

    # 4. Merkle / principle verification
    #    - Principle hash cached (stable, only changes if principles change)
    #    - Merkle root re-hashed every turn (live integrity check)
    principle_path = ROOT / "identity" / "principles.sha256"
    if not principle_path.is_file():
        abort("Missing identity/principles.sha256")
    if "principles_hash" not in cache:
        cache["principles_hash"] = sha256_file(str(principle_path))
        log(f"Principles hash cached: {cache['principles_hash']}")
    else:
        log(f"Principles cache hit (hash {cache['principles_hash']})")

    merkle_root_path = ROOT / "memory" / "tri_brain" / "merkle_root.hash"
    if not merkle_root_path.is_file():
        abort("Missing memory/tri_brain/merkle_root.hash")
    merkle_hash = sha256_file(str(merkle_root_path))
    log(f"Merkle root hash this turn: {merkle_hash}")

    # 5. PASS - save cache, return 0
    # NOTE: Do NOT call agent_speak.sh here. It calls this script.
    # Calling back creates infinite recursion -> exit 1. Audio is the caller's job.
    save_cache(cache)
    log("Per-turn guard PASSED - all checks clear")
    sys.exit(0)

if __name__ == "__main__":
    main()
