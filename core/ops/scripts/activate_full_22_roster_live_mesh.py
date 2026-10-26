#!/usr/bin/env python3
"""
activate_full_22_roster_live_mesh.py
Simultaneously executes all 22 Sovereign Citizen domain engines across Apple Silicon M4 cores,
commits bit-level receipts to each sandbox's brain, and generates a consolidated master receipt.
"""
import os
import sys
import json
import time
import importlib.util
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SANDBOXES_DIR = os.path.join(ROOT_DIR, "workspaces", "sandboxes")
MASTER_RECEIPT_PATH = os.path.join(ROOT_DIR, "memory", "catch_log", "full_22_roster_activation_master_receipt.json")

def execute_agent_engine(agent_name):
    agent_dir = os.path.join(SANDBOXES_DIR, agent_name)
    engine_file = os.path.join(agent_dir, f"{agent_name}_engine.py")
    t0 = time.perf_counter()

    if not os.path.exists(engine_file):
        return agent_name, {"status": "ENGINE_FILE_MISSING", "error": f"{engine_file} not found"}

    try:
        spec = importlib.util.spec_from_file_location(f"{agent_name}_engine", engine_file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        receipt = mod.run_experiment()
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)
        receipt["execution_wall_time_ms"] = elapsed_ms
        receipt["timestamp"] = time.time()

        # Save to agent's private brain
        brain_dir = os.path.join(agent_dir, "brain")
        os.makedirs(brain_dir, exist_ok=True)
        rec_path = os.path.join(brain_dir, "latest_activation_receipt.json")
        with open(rec_path, "w") as f:
            json.dump(receipt, f, indent=2)

        return agent_name, receipt
    except Exception as e:
        return agent_name, {"status": "EXECUTION_ERROR", "error": str(e), "elapsed_ms": round((time.perf_counter() - t0) * 1000, 3)}

def main():
    agents = sorted([
        d for d in os.listdir(SANDBOXES_DIR)
        if os.path.isdir(os.path.join(SANDBOXES_DIR, d)) and not d.startswith(".")
    ])
    print(f"=== ACTIVATING FULL 22-SOVEREIGN CITIZEN LIVE MESH ===")
    print(f"Target Citizens: {len(agents)}")

    t_start = time.perf_counter()
    master_results = {}

    with ThreadPoolExecutor(max_workers=len(agents)) as executor:
        futures = {executor.submit(execute_agent_engine, a): a for a in agents}
        for future in as_completed(futures):
            agent_name, res = future.result()
            master_results[agent_name] = res
            status = res.get("status", "UNKNOWN")
            lat = res.get("execution_wall_time_ms", 0.0)
            print(f"[+] Citizen {agent_name:12s} | Status: {status:28s} | Latency: {lat:6.2f}ms")

    total_time_ms = round((time.perf_counter() - t_start) * 1000, 2)
    master_payload = {
        "timestamp": time.time(),
        "total_active_citizens": len(master_results),
        "total_parallel_execution_time_ms": total_time_ms,
        "all_citizens_successful": all(
            res.get("status") not in ["EXECUTION_ERROR", "ENGINE_FILE_MISSING"]
            for res in master_results.values()
        ),
        "citizens": master_results
    }

    os.makedirs(os.path.dirname(MASTER_RECEIPT_PATH), exist_ok=True)
    with open(MASTER_RECEIPT_PATH, "w") as f:
        json.dump(master_payload, f, indent=2)

    print(f"\n[SUCCESS] Master activation receipt written to: {MASTER_RECEIPT_PATH}")
    print(f"Total Parallel Mesh Execution: {total_time_ms}ms across 22 sovereign agents.")

if __name__ == "__main__":
    main()
