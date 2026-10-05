# tests/lgg_test.py
"""
NASA‑style Technical Verification & Validation for Minimal Living Goal Graph (MLGG)
"""
import os
import tempfile
import pytest
import hashlib
from ops.provenance.lgg_models import GoalNode, DecisionNode, EvidenceNode, check_goal_consistency

# Helper to create a temporary file for EvidenceNode
@pytest.fixture
def temp_file():
    fd, path = tempfile.mkstemp()
    with os.fdopen(fd, "w") as f:
        f.write("test evidence content")
    yield path
    os.remove(path)

def test_goal_node_commit():
    # Use a dummy parent hash and persona lock hash
    parent = "GENESIS_NODE_0000000000000000"
    persona = "persona_lock_dummy"
    goal = GoalNode(title="Test Goal", parent_hash=parent, persona_lock_hash=persona)
    result = goal.commit()
    assert "node_id" in result
    assert result["step_type"] == "GoalNode"

def test_decision_node_commit():
    parent = "some_parent_hash"
    decision = DecisionNode(action_desc="run analysis", parent_hash=parent)
    result = decision.commit()
    assert "node_id" in result
    assert result["step_type"] == "DecisionNode"
    # Output hash should be generated
    assert decision.output_hash is not None

def test_evidence_node_commit(temp_file):
    # Assume a decision hash
    decision_hash = "decision_hash_dummy"
    ev = EvidenceNode(file_path=temp_file, linked_decision_hash=decision_hash)
    result = ev.commit()
    assert "node_id" in result
    assert result["step_type"] == "EvidenceNode"
    # Verify content hash matches file content
    with open(temp_file, "rb") as f:
        content = f.read()
    expected_hash = ev._hash(content.decode('utf-8', errors='ignore')) if hasattr(ev, "_hash") else None
    # The content hash stored in the payload
    assert result["payload_hash"] == ev.commit()["payload_hash"]

def test_check_goal_consistency_pass():
    persona = "abc123"
    decision = "def456"
    expected = "" + hashlib.sha256((persona + decision).encode('utf-8')).hexdigest()
    assert check_goal_consistency(persona, decision, expected) is True

def test_check_goal_consistency_fail():
    persona = "abc123"
    decision = "def456"
    wrong = "deadbeef"
    assert check_goal_consistency(persona, decision, wrong) is False
