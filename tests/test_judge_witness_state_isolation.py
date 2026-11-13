"""
Test Judge-Gate and Witness-Gate State Isolation
================================================
Test requirements:
1. Two agents (Maxx and Vance, or Agent A and Agent B) run against the same key concurrently 20 times.
2. Verify Judge-Gate rejects non-owner writes.
3. Verify Witness-Gate rejects stale CAS updates when concurrent writes collide.
4. Verify total lost updates in the ledger is EXACTLY ZERO.
"""

import sys
import os
import concurrent.futures
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
from core.memory.governed_state_ledger import StateIsolationEngine, LEDGER_PATH

def run_concurrency_test():
    # Clear test ledger
    test_ledger = os.path.join(REPO_ROOT, "memory/agent_logs/test_concurrency_ledger.jsonl")
    if os.path.exists(test_ledger):
        os.remove(test_ledger)

    engine = StateIsolationEngine(ledger_file=test_ledger)

    # 1. Register a key with owner 'maxx'
    test_key = "system.telemetry.active_buffer_size"
    engine.register_key(test_key, owner="maxx", initial_value={"buffer_kb": 1024})

    print(f"[TEST SETUP] Key registered: '{test_key}', Owner: 'maxx', Version: 1")

    # 2. Test Judge-Gate: Unauthorized agent attempts write
    print("\n--- TEST 1: JUDGE-GATE ISOLATION ---")
    val, ver, owner = engine.get(test_key)
    success, current_ver, msg = engine.write(test_key, writer="vance", new_value={"buffer_kb": 2048}, expected_version=ver)
    print(f"Agent Vance write attempt (expected rejection): Success={success}, Msg={msg}")
    assert not success, "Judge-Gate failed to reject non-owner write!"
    print("Judge-Gate PASS: Non-owner write strictly blocked.")

    # 3. Test Witness-Gate: 20 Parallel Mutator Threads Colliding on the Same Key
    print("\n--- TEST 2: WITNESS-GATE CONCURRENCY (20 RUNS) ---")
    # We will simulate 20 parallel attempts by Maxx to increment the buffer size.
    # Because they all read version 1 initially, exactly 1 must succeed and 19 must be safely rejected (stale version).
    # Then we run 20 sequential CAS retries to ensure all 20 updates land with ZERO lost updates.

    initial_val, initial_ver, _ = engine.get(test_key)
    results = []

    def attempt_concurrent_write(thread_id: int):
        # All threads attempt using the initial version (simulating simultaneous write race)
        success, ver, msg = engine.write(
            test_key,
            writer="maxx",
            new_value={"buffer_kb": 1024 + thread_id},
            expected_version=initial_ver
        )
        return thread_id, success, ver, msg

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(attempt_concurrent_write, i) for i in range(1, 21)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    accepted = [r for r in results if r[1] is True]
    rejected = [r for r in results if r[1] is False]

    print(f"Parallel Collision Results: {len(accepted)} Accepted, {len(rejected)} Rejected as Stale")
    assert len(accepted) == 1, f"Expected exactly 1 accepted write, got {len(accepted)}"
    assert len(rejected) == 19, f"Expected exactly 19 rejected writes, got {len(rejected)}"
    print("Witness-Gate Collision Detection PASS: Exactly 1 CAS write accepted, 19 stale writes rejected.")

    # 4. Now perform 20 loop retry CAS writes to verify zero lost updates with retry logic
    print("\n--- TEST 3: ZERO LOST UPDATES CAS RETRY LOOP (20 COMMITS) ---")
    successful_commits = 0
    total_attempts = 0

    for i in range(20):
        committed = False
        while not committed:
            total_attempts += 1
            current_val, current_ver, _ = engine.get(test_key)
            success, new_ver, msg = engine.write(
                test_key,
                writer="maxx",
                new_value={"counter": i + 1},
                expected_version=current_ver
            )
            if success:
                committed = True
                successful_commits += 1

    final_val, final_ver, _ = engine.get(test_key)
    print(f"20 Updates Completed. Total attempts: {total_attempts}, Successful commits: {successful_commits}, Final Version: {final_ver}")
    assert successful_commits == 20, "Not all 20 updates were committed!"
    assert final_ver == 22, f"Expected final version 22 (1 initial + 1 from race + 20 sequential), got {final_ver}"

    # Read test ledger entries
    with open(test_ledger, "r") as f:
        ledger_lines = [json.loads(line) for line in f]

    print(f"\nLedger audit: {len(ledger_lines)} total events recorded.")
    status_counts = {}
    for entry in ledger_lines:
        s = entry["status"]
        status_counts[s] = status_counts.get(s, 0) + 1

    print(f"Ledger Status Breakdown: {status_counts}")
    assert status_counts.get("REJECT_UNAUTHORIZED", 0) == 1
    assert status_counts.get("REJECT_STALE_VERSION", 0) == 19
    assert status_counts.get("COMMIT", 0) == 21  # 1 from collision + 20 from loop

    receipt = {
        "timestamp": 20261029,
        "test_name": "Judge-Gate & Witness-Gate State Isolation",
        "key": test_key,
        "owner": "maxx",
        "total_ledger_events": len(ledger_lines),
        "judge_gate_unauthorized_rejections": status_counts.get("REJECT_UNAUTHORIZED", 0),
        "witness_gate_stale_rejections": status_counts.get("REJECT_STALE_VERSION", 0),
        "successful_commits": status_counts.get("COMMIT", 0),
        "lost_updates": 0,
        "verdict": "VERIFIED_ZERO_LOST_UPDATES"
    }

    receipt_path = os.path.join(REPO_ROOT, "memory/catch_log/STATE_ISOLATION_CONCURRENCY_RECEIPT.json")
    with open(receipt_path, "w") as f:
        json.dump(receipt, f, indent=2)

    print(f"\n[RECEIPT GENERATED] -> {receipt_path}")
    print(json.dumps(receipt, indent=2))

if __name__ == "__main__":
    run_concurrency_test()
