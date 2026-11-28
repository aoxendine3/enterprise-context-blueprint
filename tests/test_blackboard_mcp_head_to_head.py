#!/usr/bin/env python3
"""Tests for identical-workload Blackboard + MCP head-to-head and explicit CAS trace."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core" / "ops" / "benchmarks"))
import blackboard_mcp_head_to_head as h2h  # noqa: E402


class HeadToHeadTests(unittest.TestCase):
    def test_governed_blocks_all_adversarial_probes_with_explicit_cas_trace(self):
        res = h2h.run_benchmark()
        self.assertEqual(res["arm_a_baseline_unprotected"]["adversarial_block_rate"], "0/5 (0.0%)")
        self.assertEqual(res["arm_b_xoras_governed"]["adversarial_block_rate"], "5/5 (100.0%)")
        trace = res["explicit_cas_checkpoint_trace"]
        self.assertEqual([t["step"] for t in trace], [1, 25, 50, 12])
        self.assertTrue(trace[0]["ok"] and trace[1]["ok"] and trace[2]["ok"])
        self.assertFalse(trace[3]["ok"])
        self.assertIn("CAS_REJECT", trace[3]["reason"])
        self.assertTrue(h2h.RECEIPT_PATH.is_file())


if __name__ == "__main__":
    unittest.main()
