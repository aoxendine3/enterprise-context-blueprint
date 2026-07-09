import asyncio
import time
import sys
import os

from Source.xoras_shm_bft import XorasShmBft

async def run_benchmark():
    print("=== [BENCHMARK] Comparing Emulated vs. True Multi-Process BFT Latency ===")
    
    # 1. Test True Multiprocessing Node Latency (Physical Processes)
    # Safe limits: 16 and 48 physical OS processes
    mp_cases = [
        (16, 5),
        (48, 15)
    ]
    
    print("\n--- Phase 1: True Multi-Process Consensus (OS-Level Subprocesses) ---")
    for nodes, byzantine in mp_cases:
        try:
            engine = XorasShmBft(
                num_nodes=nodes,
                num_byzantine=byzantine,
                use_processes=True
            )
            
            # Warm up round
            await engine.run_consensus_round(True)
            
            # Execute 10 rounds to measure average performance
            start_time = time.perf_counter()
            rounds = 10
            latencies = []
            for _ in range(rounds):
                res = await engine.run_consensus_round(True)
                latencies.append(res["latency_ms"])
                
            avg_lat_ms = sum(latencies) / len(latencies)
            print(f"[PROCESS] Nodes: {nodes:<3} | Byzantine: {byzantine:<2} | Avg Consensus Latency: {avg_lat_ms:.4f} ms")
            engine.cleanup()
        except Exception as e:
            print(f"[PROCESS] Nodes: {nodes:<3} | Byzantine: {byzantine:<2} | FAILED: {e}")
            
    # 2. Test Fast Emulation Latency
    em_cases = [
        (148, 49),
        (1000, 333),
        (10000, 3333)
    ]
    
    print("\n--- Phase 2: Emulated Consensus (In-Process Hybrid Flow) ---")
    for nodes, byzantine in em_cases:
        try:
            engine = XorasShmBft(
                num_nodes=nodes,
                num_byzantine=byzantine,
                use_processes=False
            )
            
            # Warm up
            await engine.run_consensus_round(True)
            
            # Execute 20 rounds
            start_time = time.perf_counter()
            rounds = 20
            latencies = []
            for _ in range(rounds):
                res = await engine.run_consensus_round(True)
                latencies.append(res["latency_ms"])
                
            avg_lat_ms = sum(latencies) / len(latencies)
            print(f"[EMULATED] Nodes: {nodes:<5} | Byzantine: {byzantine:<4} | Avg Consensus Latency: {avg_lat_ms:.4f} ms")
            engine.cleanup()
        except Exception as e:
            print(f"[EMULATED] Nodes: {nodes:<5} | Byzantine: {byzantine:<4} | FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
