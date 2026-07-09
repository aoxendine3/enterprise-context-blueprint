import asyncio
import time
import sys
import os

# Adjust path to import correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from xoras_shm_bft import XorasShmBft

async def run_stress_test():
    print("=== [STRESS TEST] Initiating Swarm SHM-BFT Scaling Limit Test ===")
    
    # Test cases: (num_nodes, num_byzantine)
    test_cases = [
        (148, 49),
        (300, 99),
        (600, 199),
        (1000, 333),
        (2000, 666),
        (3000, 999),
        (5000, 1666),
        (10000, 3333)
    ]
    
    for nodes, byzantine in test_cases:
        try:
            # Initialize engine with zero network latency simulation to check raw CPU/SHM boundaries
            engine = XorasShmBft(
                num_nodes=nodes,
                num_byzantine=byzantine,
                latency_min_ms=0.0,
                latency_max_ms=0.0
            )
            
            # Warm up
            await engine.run_consensus_round(True)
            
            # Execute 20 consensus rounds to measure average performance
            start_time = time.perf_counter()
            rounds = 20
            latencies = []
            for _ in range(rounds):
                res = await engine.run_consensus_round(True)
                latencies.append(res["latency_ms"])
                
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0 / rounds
            avg_lat_ms = sum(latencies) / len(latencies)
            
            print(f"Nodes: {nodes:<6} | Byzantine Liars: {byzantine:<5} | Consensus Round Avg: {avg_lat_ms:.4f} ms")
            
            # Cleanup engine resources
            engine.cleanup()
            
        except Exception as e:
            print(f"Nodes: {nodes:<6} | Byzantine Liars: {byzantine:<5} | FAILED with error: {e}")

if __name__ == "__main__":
    asyncio.run(run_stress_test())
