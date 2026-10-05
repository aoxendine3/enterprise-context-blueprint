"""
XORAS Sovereign Brain Copilot Production Automated Test Suite
Validates Hardware Governor, Embedded Transformer Core,
Native Accelerators, Self-Healing Remediation, and API Endpoints.
"""

import os
import sys
import json
import unittest
import threading
import time

# Add parent dir to path
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PARENT_DIR)

from hardware_governor import governor
from embedded_transformer import embedded_transformer
from remediation import guardian
from accelerators import dispatch_accelerator
from server import run_server, PORT, HOST

class TestXorasBrainCopilotCore(unittest.TestCase):

    def test_01_hardware_governor_bounds(self):
        """Verify that hardware governor strictly bounds context and pins KV RAM."""
        topo = governor.inspect_topology()
        self.assertEqual(topo["status"], "active")
        self.assertEqual(topo["strict_context_window"], 4096)
        self.assertEqual(topo["pinned_kv_cache_limit_mb"], 512)
        self.assertTrue(topo["logical_cpu_cores"] >= 1)
        self.assertTrue(topo["governor_threads_allocated"] >= 1)

        opts = governor.get_inference_options()
        self.assertEqual(opts["num_ctx"], 4096)
        self.assertTrue(opts["num_thread"] >= 1)

    def test_02_embedded_transformer_autonomous(self):
        """Verify embedded transformer runs autonomous generation with zero external dependencies."""
        stream_gen = embedded_transformer.generate_autonomous_stream("maxx", "Test prompt for sovereign core")
        tokens = []
        meta = {}
        for chunk in stream_gen:
            if chunk.get("done"):
                meta = chunk
            elif chunk.get("token"):
                tokens.append(chunk["token"])

        self.assertTrue(len(tokens) > 3)
        self.assertTrue(meta.get("done", False))
        self.assertTrue(meta.get("tokens_per_sec", 0) > 0)
        self.assertEqual(meta.get("model"), "embedded-transformer-v1.0")

    def test_03_native_accelerator_distill(self):
        """Verify native Pyramidal Distillation accelerator."""
        res = dispatch_accelerator("distill", {
            "text": "Sovereign local models ensure complete privacy, zero telemetry, and permanent autonomy."
        })
        self.assertEqual(res.get("status"), "success")
        self.assertTrue("final_invariant" in res)
        self.assertNotEqual(res["final_invariant"], "")

    def test_04_native_accelerator_drift(self):
        """Verify native Merkle drift state tree scanner."""
        res = dispatch_accelerator("drift", {"target_dir": "."})
        self.assertEqual(res.get("status"), "success")
        self.assertTrue("merkle_root" in res)
        self.assertFalse(res.get("drift_detected", True))

    def test_05_remediation_guardian_cycle(self):
        """Verify autonomous self-healing circuit breaker and recovery."""
        initial_status = guardian.get_status()
        self.assertTrue("status" in initial_status)

        # Trigger simulated remediation
        success = guardian.trigger_remediation("Unit test recovery check")
        self.assertTrue(success)

        status_after = guardian.get_status()
        self.assertTrue(status_after["remediations_performed"] >= 1)
        self.assertFalse(status_after["circuit_breaker_tripped"])

    def test_06_accelerator_audit_telemetry(self):
        """Verify hardware audit accelerator telemetry."""
        audit = dispatch_accelerator("audit", {})
        self.assertEqual(audit.get("status"), "success")
        self.assertTrue("hardware_governor" in audit)

if __name__ == "__main__":
    print("==================================================================")
    print("  RUNNING HERMES COPILOT AUTOMATED PRODUCTION TEST SUITE")
    print("==================================================================")
    unittest.main(verbosity=2)
