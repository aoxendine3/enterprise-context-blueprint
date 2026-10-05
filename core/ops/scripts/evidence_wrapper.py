# ops/scripts/evidence_wrapper.py
"""
Wrapper around the built‑in `write_to_file` function to automatically register
an EvidenceNode in the provenance DAG for every file that is created or
overwritten.
"""
import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))  # add project root to PYTHONPATH

from ops.provenance.lgg_models import EvidenceNode

def write_with_evidence(file_path: str, content: str, linked_decision_hash: str) -> None:
    """Write `content` to `file_path` and record an EvidenceNode.

    Parameters
    ----------
    file_path: str
        Destination path for the file.
    content: str
        Text to write.
    linked_decision_hash: str
        The hash of the DecisionNode that produced this artifact.
    """
    # Ensure parent directories exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    # Write the file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    # Register evidence
    ev = EvidenceNode(file_path=file_path, linked_decision_hash=linked_decision_hash)
    ev.commit()
    print(f"Evidence registered for {file_path}, node_id={ev.node_id}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: evidence_wrapper.py <file_path> <content> <linked_decision_hash>")
        sys.exit(2)
    _, fp, ct, ldh = sys.argv
    write_with_evidence(fp, ct, ldh)
    sys.exit(0)
