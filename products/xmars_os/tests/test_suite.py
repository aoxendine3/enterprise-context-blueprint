"""
XMARS.os Automated Production Verification Suite
Validates Hardware Governor, Encapsulated Transformer Core (XTC-v1),
Native x64 Kernel, Remediation Guardian, and Voice Transceiver.
"""

import os
import sys
import unittest

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PARENT_DIR)

from hardware_governor import governor
from embedded_transformer import transformer_core
from remediation import guardian
from accelerators import dispatch_accelerator

class TestXmarsOsCore(unittest.TestCase):

    def test_01_hardware_governor_bounds(self):
        """Verify that XMARS Hardware Governor strictly bounds context to 4096."""
        topo = governor.inspect_topology()
        self.assertEqual(topo["status"], "operational")
        self.assertEqual(topo["strict_context_window"], 4096)
        self.assertEqual(topo["pinned_kv_cache_limit_mb"], 512)
        self.assertTrue(topo["logical_cpu_cores"] >= 1)
        self.assertTrue(topo["governor_threads_allocated"] >= 1)

        opts = governor.get_inference_options()
        self.assertEqual(opts["num_ctx"], 4096)
        self.assertTrue(opts["num_thread"] >= 1)

    def test_02_embedded_transformer_autonomous(self):
        """Verify XTC-v1 runs autonomous generation without external dependencies."""
        stream_gen = transformer_core.generate_stream("maxx", "Verify XMARS sovereign matrix.")
        tokens = []
        meta = {}
        for chunk in stream_gen:
            if chunk.get("done"):
                meta = chunk
            elif chunk.get("token"):
                tokens.append(chunk["token"])

        self.assertTrue(len(tokens) >= 4)
        self.assertTrue(meta.get("done", False))
        self.assertTrue(meta.get("tokens_per_sec", 0) > 0)
        self.assertEqual(meta.get("model"), "xmars-transformer-core-v1.0")

    def test_03_native_accelerator_distill(self):
        """Verify XMARS Pyramidal Distillation accelerator."""
        res = dispatch_accelerator("distill", {
            "text": "XMARS.os sovereign intelligence eliminates external data leakage and ensures permanent operational integrity."
        })
        self.assertEqual(res.get("status"), "success")
        self.assertTrue("final_invariant" in res)
        self.assertNotEqual(res["final_invariant"], "")

    def test_04_native_accelerator_drift(self):
        """Verify XMARS Merkle drift state tree scanner."""
        res = dispatch_accelerator("drift", {"target_dir": "."})
        self.assertEqual(res.get("status"), "success")
        self.assertTrue("merkle_root" in res)
        self.assertFalse(res.get("drift_detected", True))

    def test_05_remediation_guardian_cycle(self):
        """Verify autonomous self-healing circuit breaker and recovery."""
        initial = guardian.get_status()
        self.assertTrue("status" in initial)

        success = guardian.execute_remediation("Test recovery cycle")
        self.assertTrue(success)

        after = guardian.get_status()
        self.assertTrue(after["remediations_executed"] >= 1)
        self.assertFalse(after["circuit_breaker_active"])

    def test_06_accelerator_audit_telemetry(self):
        """Verify XMARS hardware audit accelerator telemetry."""
        audit = dispatch_accelerator("audit", {})
        self.assertEqual(audit.get("status"), "success")
        self.assertTrue("hardware_matrix" in audit)

    def test_07_voice_transceiver_dispatch(self):
        """Verify physical voice transceiver dispatch across council."""
        res = dispatch_accelerator("speak", {
            "agent": "Maxx",
            "message": "XMARS test voice dispatch verification."
        })
        self.assertEqual(res.get("status"), "success")

if __name__ == "__main__":
    print("==================================================================")
    print("  RUNNING XMARS.os AUTOMATED PRODUCTION VERIFICATION SUITE")
    print("==================================================================")
    unittest.main(verbosity=2)
