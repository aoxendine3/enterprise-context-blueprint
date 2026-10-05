import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
from ops.provenance.context_lineage_dag_engine import ContextLineageEngine

engine = ContextLineageEngine()
payload = {
    "category": "EMPIRICAL_QUALIFICATION",
    "disposition": "KILLED_THERMODYNAMIC_FLOOR",
    "epoch_phase": "PRESENT",
    "metrics": {"joule_heating_k": 1000000.0, "max_velocity": 1000.0},
    "title": "BBQ-006 Skyrmion Racetrack Memory Verification"
}

node_info = engine.commit_step(
    session_id="session_bbq_006",
    agent_id="Vance_Falsifier",
    step_type="THERMODYNAMIC_EVALUATION",
    payload=payload
)

print(f"✅ Middle Layer Merkle Lineage committed: {node_info}")
