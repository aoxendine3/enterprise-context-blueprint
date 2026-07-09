# --- E2E Test Suite for Xoras Swarm Containment & Redirection Node ---
# Classification: [SIMULATED]

import unittest
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Source.xoras_swarm_containment import XorasSwarmContainment

class TestXorasSwarmContainment(unittest.TestCase):
    def setUp(self):
        self.containment_node = XorasSwarmContainment(num_agents=148, num_byzantine=49)

    def tearDown(self):
        self.containment_node.cleanup()

    def test_containment_healthy_agent(self):
        """Verify healthy agent is ignored and not isolated."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        res = loop.run_until_complete(
            self.containment_node.audit_and_contain(target_agent_id=10)
        )
        
        self.assertFalse(res["isolation_triggered"])
        self.assertFalse(res["isolation_committed"])
        self.assertEqual(res["target_status"], "healthy")

    def test_containment_sandbox_breach(self):
        """Verify agent with sandbox breach triggers BFT consensus and is isolated."""
        # Compromise agent 5
        self.containment_node.update_agent_telemetry(5, {"sandbox_violations": 1})
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        res = loop.run_until_complete(
            self.containment_node.audit_and_contain(target_agent_id=5)
        )
        
        self.assertTrue(res["isolation_triggered"])
        self.assertTrue(res["isolation_committed"])
        self.assertEqual(res["target_status"], "isolated")
        
        # Verify it logged in the containment ledger
        self.assertEqual(len(self.containment_node.isolation_log), 1)
        self.assertEqual(self.containment_node.isolation_log[0]["agent_id"], 5)

    def test_containment_latency_violation(self):
        """Verify agent with high latency (> 500ms) triggers BFT consensus and is isolated."""
        # Force high latency on agent 22
        self.containment_node.update_agent_telemetry(22, {"latency_ms": 600.0})
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        res = loop.run_until_complete(
            self.containment_node.audit_and_contain(target_agent_id=22)
        )
        
        self.assertTrue(res["isolation_triggered"])
        self.assertTrue(res["isolation_committed"])
        self.assertEqual(res["target_status"], "isolated")

    def test_sub_millisecond_containment_speed(self):
        """Verify the full audit + consensus process completes in under 1ms."""
        self.containment_node.update_agent_telemetry(8, {"sandbox_violations": 1})
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Warmup
        loop.run_until_complete(self.containment_node.audit_and_contain(target_agent_id=8))
        
        latencies = []
        for _ in range(5):
            res = loop.run_until_complete(
                self.containment_node.audit_and_contain(target_agent_id=8)
            )
            latencies.append(res["elapsed_ms"])
            
        avg_latency = sum(latencies) / len(latencies)
        print(f"\n[BENCHMARK] Swarm Containment Average Speed: {avg_latency:.3f} ms")
        
        self.assertLess(avg_latency, 1.0)

if __name__ == '__main__':
    unittest.main()
