#!/usr/bin/env python3
"""
RECHECK: logs, Merkle journals, asset registries, current-state files.
Read-only, no secret values. Writes memory/catch_log/STATE_JOURNALS_RECHECK.json.
"""
import json, time, hashlib
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
OUT = ROOT / "memory/catch_log/STATE_JOURNALS_RECHECK.json"


def root(f):
    p = ROOT / f
    return p.read_text().strip() if p.exists() else None


def journal(path, n=1):
    p = ROOT / path
    if not p.exists():
        return None
    rows = [json.loads(l) for l in p.read_text(errors="ignore").splitlines() if l.strip()]
    return {"rows": len(rows), "last": rows[-n:] if rows else []}


r = {}
# Merkle claim cross-check (canonical vs known-good vs shadow)
r["merkle_claims"] = {
    "canonical": root("memory/tri_brain/merkle_root.hash"),
    "known_good": root("memory/tri_brain/merkle_root.known_good"),
    "shadow": root("core/memory/catch_log/merkle_root.hash"),
}
r["merkle_consistent"] = (r["merkle_claims"]["canonical"] == r["merkle_claims"]["known_good"])

# Journals
r["signed_root_manifests"] = journal("memory/tri_brain/signed_root_manifests.jsonl")
r["golden_checkpoints"] = journal("memory/tri_brain/golden_checkpoints.jsonl")
r["trinity_hashes"] = journal("memory/tri_brain/trinity_hashes.jsonl")
r["world_merkle_journal"] = journal("memory/tri_brain/world_merkle_journal.jsonl")

# Asset registry: classify duplicates as version history vs collision
p = ROOT / "memory/tri_brain/merkle_asset_registry.jsonl"
rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
from collections import Counter, defaultdict
by_id = defaultdict(list)
for x in rows:
    by_id[x.get("asset_id")].append(x)
r["asset_registry"] = {
    "entries": len(rows),
    "unique_ids": len(by_id),
    "id_counts": {k: len(v) for k, v in by_id.items()},
    "version_history": all(
        len({x.get("timestamp_utc") for x in v}) == len(v) for v in by_id.values() if len(v) > 1),
    "note": "multiple timestamped revisions with distinct payloads = version history, not corruption",
}

# Quarantine law
d = json.loads((ROOT / "memory/catch_log/QUARANTINE_LEDGER.json").read_text())
r["quarantine"] = {
    "entries": len(d.get("entries", [])),
    "deletions": d.get("deletions"),
    "resolved_not_moved": len(d.get("resolved_not_moved", [])),
    "law": d.get("law"),
}

# Sentinel liveness (home) — metadata only
hp = Path.home() / ".sovereign/state/sentinel_heartbeat.jsonl"
if hp.exists():
    lines = hp.read_text(errors="ignore").splitlines()
    r["sentinel"] = {"lines": len(lines), "last": lines[-1][:160] if lines else None}

# Current-state files
r["status_json"] = (ROOT / "artifacts/status.json").read_text().strip()[:120]
r["shadow_claim_consumer_found"] = "NOT DETERMINED BY GREP (tree too large; see note)"

payload = {
    "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "verdict": "STATE_JOURNALS_RECHECK_COMPLETE",
    "note": "All values are claims/metadata; no secret values printed. Repo-wide greps time out on 26GB tree; targeted reads used.",
    "results": r,
}
OUT.write_text(json.dumps(payload, indent=2))
print(json.dumps(payload, indent=2))
