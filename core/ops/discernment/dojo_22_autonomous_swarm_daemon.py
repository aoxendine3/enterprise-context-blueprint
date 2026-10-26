#!/usr/bin/env python3
"""
dojo_22_autonomous_swarm_daemon.py
Continuous Autonomous Deep Work Daemon for the 22 Sovereign Citizens.
Executes non-stop cycles, recording every citizen activity into the
Sovereign Durable Workflow SQLite WAL engine with Merkle leaf hashes.
"""
import os
import sys
import time
import json
import importlib.util
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT_DIR = Path(__file__).resolve().parents[3]
SANDBOXES_DIR = ROOT_DIR / "workspaces" / "sandboxes"
sys.path.insert(0, str(ROOT_DIR / "core" / "ops" / "temporal"))
from sovereign_durable_workflow_engine import SovereignDurableWorkflowEngine

engine = SovereignDurableWorkflowEngine()

def run_citizen_task(agent_name: str, workflow_id: str):
    engine_file = SANDBOXES_DIR / agent_name / f"{agent_name}_engine.py"
    t0 = time.perf_counter()
    if not engine_file.exists():
        return agent_name, {"status": "ENGINE_MISSING"}

    try:
        spec = importlib.util.spec_from_file_location(f"{agent_name}_engine", str(engine_file))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        receipt = mod.run_experiment()
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)
        receipt["wall_time_ms"] = elapsed_ms

        # Record into Durable SQLite WAL Engine
        rec = engine.record_activity_completion(
            workflow_id=workflow_id,
            activity_name=f"{agent_name.capitalize()}DomainExecution",
            citizen_agent=agent_name,
            output=receipt
        )
        receipt["durable_sequence"] = rec["sequence"]
        receipt["merkle_leaf_hash"] = rec["leaf_hash"]
        return agent_name, receipt
    except Exception as e:
        return agent_name, {"status": "ERROR", "error": str(e)}

def run_single_swarm_cycle(cycle_id: int):
    workflow_id = f"swarm_cycle_{cycle_id}_{int(time.time())}"
    engine.start_workflow(
        workflow_id=workflow_id,
        workflow_type="DojoSwarmContinuousDeepWork",
        initial_input={"cycle": cycle_id, "timestamp": time.time(), "citizens_target": 22}
    )

    citizens = sorted([
        d.name for d in SANDBOXES_DIR.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ])

    cycle_t0 = time.perf_counter()
    cycle_receipts = {}

    with ThreadPoolExecutor(max_workers=len(citizens)) as pool:
        futures = {pool.submit(run_citizen_task, c, workflow_id): c for c in citizens}
        for fut in as_completed(futures):
            c_name, res = fut.result()
            cycle_receipts[c_name] = res

    total_cycle_ms = round((time.perf_counter() - cycle_t0) * 1000, 2)
    print(f"Cycle {cycle_id:04d} Complete | Workflow: {workflow_id} | Total Time: {total_cycle_ms}ms | Active Citizens: {len(cycle_receipts)}/22")
    return workflow_id, cycle_receipts

if __name__ == "__main__":
    print("=== STARTING 22-CITIZEN AUTONOMOUS SWARM DAEMON ===")
    is_daemon = "--daemon" in sys.argv or "--continuous" in sys.argv
    cycle = 1
    try:
        while True:
            wf, r = run_single_swarm_cycle(cycle)
            successes = sum(1 for res in r.values() if res.get("status") != "ERROR")
            if not is_daemon and cycle >= 5:
                break
            cycle += 1
            time.sleep(2.0)
    except KeyboardInterrupt:
        print("\n[!] Swarm daemon stopped cleanly.")
    print(f"\n[SUCCESS] Continuous Swarm Daemon executed {cycle} cycles with durable event-sourced replay.")
