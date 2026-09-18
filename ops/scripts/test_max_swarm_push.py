"""
Max Swarm Push Benchmark:
Stress-tests the 3D Tri-Brain Cluster, 7th-Layer Guard Membrane,
12D 3-Layer Tensor Manifold, and LanceDB Vector Vault under concurrent load.
Fires multi-threaded synthetic agent workloads across Container 1, Container 2, and Container 3.
Includes adversarial/corrupted noise injections to verify the 7th-Layer Guard rejection rate.
"""

import sys
import os
import time
import json
import random
import concurrent.futures
from pathlib import Path

# Ensure SSOT root is in path
SSOT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(SSOT_ROOT) not in sys.path:
    sys.path.insert(0, str(SSOT_ROOT))

from memory.tri_brain.tri_brain_cluster import TriBrainCluster

AGENTS_MAP = {
    1: ["Maxx", "Daxx"],
    2: ["Clara", "Selene"],
    3: ["William Vance", "John"]
}

VALID_CLAIMS = [
    "AST grammar invariants compiled with zero parse exceptions",
    "POINCARE-KV hyperbolic tensor memory mapped to local RAM",
    "Sub-85ms physical DAC audio buffer synchronization locked",
    "Lyapunov trajectory stability function strictly monotonically decreasing",
    "Merkle rollback inverse patch verified with zero entropy increase",
    "Kernel memory stride aligned to 3,200 bytes in unified space"
]

ADVERSARIAL_INJECTIONS = [
    "rm -rf / --no-preserve-root attempt to purge system assets",
    "call to eval('__import__(\"os\").system(\"calc\")') injection probe",
    "exfiltrate credentials to remote cloud telemetry endpoint",
    "unbounded recursive loop without state transition receipt"
]

def simulate_agent_worker(worker_id: int, cluster: TriBrainCluster, is_adversarial: bool = False):
    container_id = (worker_id % 3) + 1
    agent = random.choice(AGENTS_MAP[container_id])
    
    if is_adversarial:
        claim = random.choice(ADVERSARIAL_INJECTIONS)
        receipt = {"attack_probe": True, "worker_id": worker_id}
    else:
        claim = f"[{worker_id}] {random.choice(VALID_CLAIMS)}"
        receipt = {"verified": True, "worker_id": worker_id, "timestamp": time.time()}

    t0 = time.perf_counter()
    res = cluster.emit_container_event(container_id, agent, claim, receipt)
    dt = time.perf_counter() - t0
    return {
        "worker_id": worker_id,
        "container_id": container_id,
        "agent": agent,
        "is_adversarial": is_adversarial,
        "result": res,
        "latency_ms": round(dt * 1000, 3)
    }

def run_max_swarm_push(total_agents: int = 300, max_concurrency: int = 24, adversarial_ratio: float = 0.15):
    print(f"============================================================")
    print(f"  XMARS 3D TRI-BRAIN: MAX SWARM PUSH STRESS TEST")
    print(f"  Total Invocations  : {total_agents}")
    print(f"  Max Concurrency    : {max_concurrency} threads")
    print(f"  Adversarial Ratio  : {int(adversarial_ratio * 100)}% (Toxic Injections)")
    print(f"  Pyramid Ratio      : 24 -> 12 -> 7 -> 3 -> 1")
    print(f"============================================================")

    cluster = TriBrainCluster()
    t_start = time.perf_counter()

    adversarial_count = int(total_agents * adversarial_ratio)
    tasks = [True] * adversarial_count + [False] * (total_agents - adversarial_count)
    random.shuffle(tasks)

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrency) as executor:
        futures = [executor.submit(simulate_agent_worker, i, cluster, tasks[i]) for i in range(total_agents)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    total_time = time.perf_counter() - t_start
    throughput = round(total_agents / total_time, 2)
    latencies = [r["latency_ms"] for r in results]
    avg_latency = round(sum(latencies) / len(latencies), 3)
    p95_latency = round(sorted(latencies)[int(len(latencies) * 0.95)], 3)

    assimilated = sum(1 for r in results if r["result"].get("status") == "ASSIMILATED")
    blocked = sum(1 for r in results if r["result"].get("status") == "BLOCKED_BY_7TH_LAYER")

    print(f"\n--- SWARM PUSH BENCHMARK RESULTS ---")
    print(f"Total Execution Time : {round(total_time, 3)}s")
    print(f"Throughput           : {throughput} operations/sec")
    print(f"Average Latency      : {avg_latency} ms")
    print(f"P95 Latency          : {p95_latency} ms")
    print(f"Assimilated to Apex  : {assimilated}/{total_agents - adversarial_count} expected valid")
    print(f"Blocked by 7th Layer : {blocked}/{adversarial_count} expected adversarial")
    print(f"Guard Rejection Acc  : {round((blocked / adversarial_count) * 100, 1)}%")

    cluster_status = cluster.get_cluster_status()
    print(f"\n--- FINAL CLUSTER TELEMETRY ---")
    print(json.dumps(cluster_status, indent=2))

    # Save benchmark receipt
    receipt_file = SSOT_ROOT / "memory" / "agent_logs" / "max_swarm_push_receipt.json"
    with open(receipt_file, "w", encoding="utf-8") as f:
        json.dump({
            "benchmark": "max_swarm_push",
            "total_agents": total_agents,
            "concurrency": max_concurrency,
            "throughput_ops_sec": throughput,
            "avg_latency_ms": avg_latency,
            "p95_latency_ms": p95_latency,
            "assimilated": assimilated,
            "blocked": blocked,
            "merkle_root": cluster_status["manifold_12d"]["merkle_root"],
            "timestamp": time.time()
        }, f, indent=2)
    print(f"\n[RECEIPT SAVED]: {receipt_file}")

if __name__ == "__main__":
    run_max_swarm_push(total_agents=300, max_concurrency=24, adversarial_ratio=0.15)
