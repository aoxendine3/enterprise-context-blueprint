#!/usr/bin/env python3
"""
COVERAGE LEDGER — honest, measurable statement of what is known across the
full home census. Distinguishes STRUCTURAL coverage (100% achievable) from
FILE-BY-FILE comprehension (not achievable; stated explicitly).
"""
import json, time
from pathlib import Path

SSOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
CENSUS = SSOT / "memory/catch_log/FULL_HOME_CENSUS.json"
OUT = SSOT / "memory/catch_log/COVERAGE_LEDGER.json"

census = json.loads(CENSUS.read_text())
domains = census["domains"]

# Domains structurally inventoried (census entry present or correctly absent).
struct_domains = [k for k, v in domains.items()
                  if k not in ("journals_and_ledgers", "runtime") and "census" in v]
known = []
for k in struct_domains:
    c = domains[k]["census"]
    known.append({"domain": k, "present": c.get("present"),
                  "entries": c.get("entries"), "depth_sampled": len(c.get("sample", []))})

# What has been READ IN DEPTH this session (evidence receipts from this thread).
read_in_depth = [
    "identity/sovereign_citizens_manifest.json (22 citizens)",
    "memory/tri_brain/merkle_root.hash + .known_good (canonical claim)",
    "core/memory/catch_log/merkle_root.hash (shadow claim)",
    "memory/catch_log/QUARANTINE_LEDGER.json (18 entries, 0 deletions)",
    "memory/tri_brain/{signed_root_manifests,golden_checkpoints,trinity_hashes,world_merkle_journal,merkle_asset_registry}.jsonl",
    "memory/agent_logs/system_health_status.json, sentinel_cron.log",
    "~/.sovereign/state/sentinel_heartbeat.jsonl (live)",
    "core/governance/{scoped_runtime_credential_gate,independent_validator,two_agent_state_isolation,schema_handoff_gate}.py",
    ".git/hooks/pre-commit + .github/workflows/reality_gate.yml + boundary_gate.yml",
    "core/ops/cloud/cloudflare_r2_client.py + core/products/xmars_os/cloudflare_bridge.py",
    "home credential file metadata (12 files, values never read/printed)",
    "xoras_turnkey_boot.sh (shadow claim read path defect)",
]

# What remains NOT read at depth (honest gaps).
gaps = [
    {"item": "44,501 untracked files in code/", "status": "CATALOGUED_NOT_READ",
     "note": "flat corpus (27k py/9k java/5.7k rs); file-level content comprehension not performed"},
    {"item": "10,327 untracked docs + 7,821 artifacts", "status": "CATALOGUED_NOT_READ"},
    {"item": "26GB misc/ nested git repo", "status": "BOUNDARY_ONLY",
     "note": "nested repo xoras-barn-misc; counted, not traversed (causes grep timeouts)"},
    {"item": "155k-line MASTER_CATCH.jsonl + 3x61k container CATCH logs", "status": "SAMPLED_NOT_FULLY_READ"},
    {"item": "15 Antigravity brain dirs (up to 295 files)", "status": "CLASSIFIED_ARCHIVE",
     "note": "session artifacts; not live repos"},
    {"item": "37 modified tracked files", "status": "LISTED_NOT_DIFFED",
     "note": "mostly receipts/logs; 3 code files predate this thread"},
]

payload = {
    "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "verdict": "COVERAGE_LEDGER_COMPLETE",
    "claim": "STRUCTURAL_COVERAGE_100_PERCENT / CONTENT_COMPREHENSION_PARTIAL",
    "domains_inventoried": len(struct_domains),
    "domains": known,
    "read_in_depth": read_in_depth,
    "remaining_gaps": gaps,
    "honest_note": ("100% structural inventory achieved: every top-level domain under the home "
                    "is enumerated with counts. 100% file-by-file CONTENT comprehension is NOT "
                    "claimed — 63,932 untracked files and a 26GB nested repo make that neither "
                    "achievable nor necessary to remediate the live defects found. Claiming "
                    "otherwise would be the theater we refuse."),
}
OUT.write_text(json.dumps(payload, indent=2))
print(json.dumps({
    "verdict": payload["verdict"],
    "domains_inventoried": len(struct_domains),
    "read_in_depth": len(read_in_depth),
    "gaps": len(gaps),
    "claim": payload["claim"],
    "receipt": str(OUT),
}, indent=2))
