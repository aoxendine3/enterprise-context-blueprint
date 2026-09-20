#!/usr/bin/env python3
"""
XORAS SYSTEM: SOVEREIGN CITIZEN CAPSULE DEPLOYER
Instantiates isolated agent houses for Lead 9 roster.
Eliminates memory bleed by providing private sqlite + vector manifolds for each citizen.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
ROSTER_PATH = ROOT / "identity" / "lead9_roster.json"
CITIZENS_DIR = ROOT / "agents" / "citizens"

def deploy():
    with open(ROSTER_PATH, "r", encoding="utf-8") as f:
        roster = json.load(f)

    for member in roster["lead_9"]:
        agent_id = member["agent_id"]
        house = CITIZENS_DIR / agent_id
        brain_dir = house / "brain"
        vector_dir = brain_dir / "vector_hexagraph"
        house.mkdir(parents=True, exist_ok=True)
        vector_dir.mkdir(parents=True, exist_ok=True)
        
        identity = {
            "agent_id": agent_id,
            "name": member["name"],
            "role": member["role"],
            "seat": member["seat"],
            "status": "SOVEREIGN_CITIZEN_ACTIVE",
            "isolation_level": "ZERO_BLEED_CAPSULE_ISOLATED",
            "authority": "LOG_ENTRY_072_CONSTITUTIONAL"
        }
        with open(house / "identity.json", "w", encoding="utf-8") as f:
            json.dump(identity, f, indent=2)
            
        rules_md = f"""# Operational Rules: {member["name"]} ({member["role"]})

## Sovereign Identity
- ID: `{agent_id}`
- Seat: {member["seat"]}
- Isolation Boundary: Strictly confined to `agents/citizens/{agent_id}/`

## Memory Bleed Invariants
1. Private memory lives in `brain/short_term.sqlite` and `brain/vector_hexagraph/`.
2. Communication with peer agents is routed via `world_file.db` blackboard and signed MTPO advisory signals.
3. No raw unvalidated state may pollute peer agent capsules.
"""
        with open(house / "rules.md", "w", encoding="utf-8") as f:
            f.write(rules_md)

    print(f"Successfully deployed {len(roster['lead_9'])} Sovereign Citizen Capsules into {CITIZENS_DIR}")

if __name__ == "__main__":
    deploy()
