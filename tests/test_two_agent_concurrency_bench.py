"""
Two Agents Concurrent 20-Run Benchmark
======================================
Step 3 Implementation:
- Agent A (Owner: Maxx) and Agent B (Proposer/Collaborator: Vance).
- Both attempt 20 operations against the same shared key in parallel threads.
- Verifies:
  1. Unauthorized non-owner direct writes are rejected fail-closed.
  2. Stale versions are rejected via CAS.
  3. Governed proposal/commit workflow produces exactly 20 updates.
  4. Lost updates in the ledger == ZERO.
"""

import sys
import os
import json
import threading
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
from core.governance.two_agent_state_isolation import GovernedSharedStateManager

def run_two_agent_parallel_test():
    ledger_path = os.path.join(REPO_ROOT, "memory/agent_logs/two_agent_concurrency_ledger.jsonl")
    if os.path.exists(ledger_path):
        os.remove(ledger_path)

    mgr = GovernedSharedStateManager(ledger_path)

    # Step 1: Maxx is registered as the sole owner of the shared counter
    shared_key = "cluster.distributed_tx_counter"
    mgr.register_key(shared_key, owner="Maxx", initial_value=0)

    # 1. Direct Proof of Judge-Gate: Vance attempts direct write -> REJECTED
    val, ver, owner = mgr.read_state(shared_key)
    ok, cur_ver, msg = mgr.commit_direct(shared_key, agent="Vance", new_value=999, expected_version=ver)
    assert not ok, "Judge-Gate failed to reject non-owner direct write!"
    print(f"[JUDGE-GATE VERIFIED] Non-owner direct write rejected: {msg}")

    # 2. Parallel 20-Run Test:
    # 20 operations to be performed.
    # Agent Vance submits 10 proposals; Agent Maxx performs 10 direct updates.
    # Both agents run concurrently across 2 threads racing on the same key.
    print("\n--- RUNNING 20 CONCURRENT OPERATIONS (MAXX & VANCE) ---")

    maxx_successes = 0
    vance_successes = 0
    stale_rejections = 0

    def maxx_worker():
        nonlocal maxx_successes, stale_rejections
        for _ in range(10):
            committed = False
            while not committed:
                val, ver, _ = mgr.read_state(shared_key)
                # Maxx increments directly
                ok, new_ver, msg = mgr.commit_direct(shared_key, agent="Maxx", new_value=val + 1, expected_version=ver)
                if ok:
                    committed = True
                    maxx_successes += 1
                else:
                    stale_rejections += 1
                    time.sleep(0.001)

    def vance_worker():
        nonlocal vance_successes, stale_rejections
        for _ in range(10):
            committed = False
            while not committed:
                val, ver, _ = mgr.read_state(shared_key)
                # Vance proposes delta = 1 based on current version
                prop_id = mgr.propose_change(shared_key, proposer="Vance", delta=1, base_version=ver)
                # Maxx (owner) commits the proposal with CAS check
                ok, new_ver, msg = mgr.owner_review_and_commit_proposal(shared_key, owner_agent="Maxx", proposal_id=prop_id)
                if ok:
                    committed = True
                    vance_successes += 1
                else:
                    stale_rejections += 1
                    time.sleep(0.001)

    t1 = threading.Thread(target=maxx_worker)
    t2 = threading.Thread(target=vance_worker)

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    # Final Verification
    final_val, final_ver, final_owner = mgr.read_state(shared_key)
    print(f"\nExecution Complete:")
    print(f"Maxx Direct Commits: {maxx_successes}")
    print(f"Vance Proposed & Committed Updates: {vance_successes}")
    print(f"Stale Version Rejections Handled: {stale_rejections}")
    print(f"Final Counter Value: {final_val} (Expected: 20)")
    print(f"Final Version: v{final_ver} (Expected: v21)")

    # Assertions
    assert maxx_successes == 10, f"Maxx expected 10 commits, got {maxx_successes}"
    assert vance_successes == 10, f"Vance expected 10 commits, got {vance_successes}"
    assert final_val == 20, f"Counter mismatch: expected 20, got {final_val}"
    assert final_ver == 21, f"Version mismatch: expected 21 (1 initial + 20 updates), got {final_ver}"

    # Read and audit ledger
    with open(ledger_path, "r") as f:
        records = [json.loads(line) for line in f]

    commits = [r for r in records if r["status"] == "COMMITTED"]
    lost_updates = 20 - len(commits)
    print(f"Total Ledger Records: {len(records)}")
    print(f"Total Committed Writes: {len(commits)}")
    print(f"Lost Updates in Ledger: {lost_updates}")

    assert lost_updates == 0, f"Lost updates detected! Count: {lost_updates}"

    # Write Machine Receipt
    receipt = {
        "benchmark": "Two-Agent Concurrency & State Isolation 20-Run Test",
        "key": shared_key,
        "owner_agent": "Maxx",
        "collaborator_agent": "Vance",
        "operations_run": 20,
        "maxx_direct_commits": maxx_successes,
        "vance_proposals_committed": vance_successes,
        "stale_rejections_intercepted": stale_rejections,
        "total_committed_updates": len(commits),
        "lost_updates": 0,
        "final_state_value": final_val,
        "final_version": final_ver,
        "verdict": "ZERO_LOST_UPDATES_PROVEN",
        "ledger_file": ledger_path
    }

    receipt_path = os.path.join(REPO_ROOT, "memory/catch_log/TWO_AGENT_ZERO_LOST_UPDATES_RECEIPT.json")
    with open(receipt_path, "w") as f:
        json.dump(receipt, f, indent=2)

    print(f"\n[RECEIPT SAVED] -> {receipt_path}")
    print(json.dumps(receipt, indent=2))

if __name__ == "__main__":
    run_two_agent_parallel_test()
