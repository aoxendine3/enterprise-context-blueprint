# ops/scripts/check_consistency.py
"""
Lightweight consistency check for a new GoalNode.
Ensures that the aggregated hash of the persona lock and the latest decision
matches the expected aggregate stored on the persona‑lock node.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))  # add project root to PYTHONPATH

from ops.provenance.lgg_models import check_goal_consistency

def main(persona_lock_hash: str, latest_decision_hash: str, expected_agg: str) -> int:
    if check_goal_consistency(persona_lock_hash, latest_decision_hash, expected_agg):
        print("CONSISTENCY PASS")
        return 0
    else:
        print("CONSISTENCY FAIL")
        return 1

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: check_consistency.py <persona_lock_hash> <latest_decision_hash> <expected_agg>")
        sys.exit(2)
    _, plh, ldh, exp = sys.argv
    sys.exit(main(plh, ldh, exp))
