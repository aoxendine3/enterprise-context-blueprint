# --- E2E Test Suite for Xoras SHM-BFT Consensus Engine ---
# Classification: [SIMULATED]

import unittest
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Source.xoras_shm_bft import XorasShmBft

class TestXorasShmBft(unittest.TestCase):
    def setUp(self):
        # Configure standard 148 nodes with 49 Byzantine faults
        # Minimum latency set to 0 to test raw throughput capability
        self.consensus_engine = XorasShmBft(
            num_nodes=148,
            num_byzantine=49,
            latency_min_ms=0.0,
            latency_max_ms=0.0
        )

    def tearDown(self):
        self.consensus_engine.cleanup()

    def test_byzantine_agreement_success(self):
        """Verify 148 nodes (with 49 Byzantine liars) reach correct consensus."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        res = loop.run_until_complete(
            self.consensus_engine.run_consensus_round(proposal_value=True)
        )
        
        self.assertTrue(res["consensus_reached"])
        self.assertEqual(res["final_value"], True)
        self.assertEqual(res["honest_nodes_reporting"], 99) # 148 - 49 honest nodes
        
    def test_byzantine_agreement_false_proposal(self):
        """Verify consensus on False proposal is reached correctly."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        res = loop.run_until_complete(
            self.consensus_engine.run_consensus_round(proposal_value=False)
        )
        
        self.assertTrue(res["consensus_reached"])
        self.assertEqual(res["final_value"], False)

    def test_sub_millisecond_consensus_benchmark(self):
        """Assert BFT consensus achieves sub-millisecond execution time."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Warmup
        loop.run_until_complete(self.consensus_engine.run_consensus_round(proposal_value=True))
        
        latencies = []
        for _ in range(5):
            res = loop.run_until_complete(
                self.consensus_engine.run_consensus_round(proposal_value=True)
            )
            latencies.append(res["latency_ms"])
            
        avg_latency = sum(latencies) / len(latencies)
        print(f"\n[BENCHMARK] SHM-BFT Average Consensus Latency: {avg_latency:.3f} ms")
        
        # Bounded check (must be < 1.0 ms)
        self.assertLess(avg_latency, 1.0)

    def test_invalid_nodes_limit_error(self):
        """Verify configuring BFT with insufficient honest nodes (> 1/3 Byzantine) raises error."""
        with self.assertRaises(ValueError):
            XorasShmBft(num_nodes=10, num_byzantine=4) # 10 < 3*4 + 1 = 13 (fails)

if __name__ == '__main__':
    unittest.main()
