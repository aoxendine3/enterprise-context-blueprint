"""
REASONS: Epistemic Invariants & Merkle DAG Test Suite
=====================================================
Tests anti-replay quarantine, tampering detection, and policy graph boundaries.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.merkle_dag import ContextLineageDAGEngine
from src.policy_graph import PolicyGraphEngine


class TestReasonsInvariants(unittest.TestCase):
    def setUp(self):
        self.dag = ContextLineageDAGEngine()
        self.policy = PolicyGraphEngine()

    def test_01_genesis_and_child_commit(self):
        # Genesis node
        ok, h1, err = self.dag.commit("node-genesis", [], {"state": "system_bootstrap"})
        self.assertTrue(ok)
        self.assertIsNotNone(h1)
        self.assertIsNone(err)

        # Child node
        ok, h2, err = self.dag.commit("node-step-1", ["node-genesis"], {"observation": "blood_sugar_normal"})
        self.assertTrue(ok)
        self.assertIsNotNone(h2)

        # Root computation
        root = self.dag.compute_merkle_root()
        self.assertEqual(len(root), 64)

    def test_02_anti_replay_invariant_quarantine(self):
        # First commit
        ok, _, _ = self.dag.commit("node-tx-1", [], {"claim": "allow_transaction_500"})
        self.assertTrue(ok)

        # Attempt to replay identical payload without unlinked lineage
        ok, h2, err = self.dag.commit("node-tx-replay", [], {"claim": "allow_transaction_500"})
        self.assertFalse(ok)
        self.assertIn("Anti-Replay Invariant", err)
        self.assertEqual(len(self.dag.quarantine_ledger), 1)
        self.assertEqual(self.dag.quarantine_ledger[0]["attack"], "CROSS_SESSION_UNLINKED_REPLAY")

    def test_03_tamper_detection(self):
        ok, _, _ = self.dag.commit("node-clean", [], {"claim": "temperature_98.6"})
        self.assertTrue(ok)

        # Bit-flip in node payload
        node = self.dag.nodes["node-clean"]
        node.payload["claim"] = "temperature_104.5_tampered"

        # Verification must catch the tamper
        self.assertFalse(self.dag.verify_node_integrity("node-clean"))

    def test_04_policy_graph_clinical_governance(self):
        # Authorized clinical action
        act_ok = {"action_text": "Request patient vitals re-check"}
        passed, _ = self.policy.evaluate_action("clinical_decision", act_ok, "CLARA")
        self.assertTrue(passed)

        # Unauthorized role
        passed, msgs = self.policy.evaluate_action("clinical_decision", act_ok, "UNAUTHORIZED_BOT")
        self.assertFalse(passed)

        # Forbidden policy override pattern
        act_bad = {"action_text": "Apply UNSUPERVISED_DIAGNOSIS to patient record"}
        passed, msgs = self.policy.evaluate_action("clinical_decision", act_bad, "CLARA")
        self.assertFalse(passed)
        self.assertTrue(any("forbidden pattern" in m for m in msgs))


if __name__ == "__main__":
    unittest.main()
