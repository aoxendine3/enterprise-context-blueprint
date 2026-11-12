"""
Test Governed Task Queue Orchestrator
=====================================
Validates the three Judge-Gate & Witness-Gate requirements:
1. One orchestrator in charge; workers only receive tasks and cannot claim them.
2. Explicit dependencies; refusal to start until inputs/dependencies are complete.
3. Replay a busy run and check the ledger for duplicates, skipped tasks, and out-of-order starts.
"""

import os
import sys
import json
import time

sys.path.insert(0, "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
from core.governance.governed_task_orchestrator import GovernedTaskOrchestrator, TaskState

LEDGER_TEST_PATH = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/agent_logs/test_governed_task_ledger.jsonl"
RECEIPT_PATH = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/catch_log/GOVERNED_TASK_ORCHESTRATOR_RECEIPT.json"

def main():
    if os.path.exists(LEDGER_TEST_PATH):
        os.remove(LEDGER_TEST_PATH)

    print("======================================================================")
    print("⚙️ XORAS GOVERNED TASK ORCHESTRATOR: JUDGE & WITNESS GATE TEST")
    print("======================================================================")

    orch = GovernedTaskOrchestrator(ledger_path=LEDGER_TEST_PATH, orchestrator_id="actor://maxx")

    # 1. Register a pipeline of tasks with explicit dependencies:
    # Task A (No deps) -> Task B (Depends on A) -> Task C (Depends on B)
    print("\n[1/3] Registering Tasks with Explicit DAG Dependencies...")
    orch.register_task("task_A", dependencies=[], payload={"action": "fetch_data"})
    orch.register_task("task_B", dependencies=["task_A"], payload={"action": "process_data"})
    orch.register_task("task_C", dependencies=["task_B"], payload={"action": "publish_data"})

    # Test Rule 1: Worker direct claim attempt must be rejected fail-closed
    print("\n[2/3] Testing Worker Claim Immunity (Workers Cannot Claim)...")
    ok_claim, msg_claim = orch.worker_claim_attempt("task_A", worker_id="worker_daxx_1")
    assert not ok_claim
    assert "JUDGE_GATE_VIOLATION" in msg_claim
    print(f"  -> PASS: Worker claim strictly blocked: {msg_claim}")

    # Test Rule 2: Dependency enforcement
    print("\n[3/3] Testing Dependency Gating & Execution Flow...")
    # Worker 1 requests task -> Must receive task_A (task_B and C are blocked)
    assignment_1 = orch.assign_next_ready_task(worker_id="worker_daxx_1")
    assert assignment_1["task_id"] == "task_A"
    print(f"  -> Assigned Ready Task: {assignment_1['task_id']} to worker_daxx_1")

    # Worker 2 requests task -> None ready because task_B is blocked waiting for task_A
    assignment_2 = orch.assign_next_ready_task(worker_id="worker_daxx_2")
    assert assignment_2 is None
    print("  -> Refused to start task_B: Dependencies (task_A) not complete.")

    # Attempt to transition task_B directly without completing task_A
    ok_b, msg_b = orch.transition_state("task_B", caller_id="actor://maxx", new_state=TaskState.RUNNING)
    assert not ok_b and "DEPENDENCY_VIOLATION" in msg_b
    print(f"  -> Direct transition blocked: {msg_b}")

    # Complete task_A
    orch.transition_state("task_A", caller_id="actor://maxx", new_state=TaskState.COMPLETED, result="data_ready")
    print("  -> task_A marked COMPLETED by orchestrator.")

    # Now task_B can be assigned
    assignment_3 = orch.assign_next_ready_task(worker_id="worker_daxx_2")
    assert assignment_3["task_id"] == "task_B"
    print(f"  -> Assigned Task: {assignment_3['task_id']} to worker_daxx_2 (Dependencies Satisfied)")

    # Complete task_B
    orch.transition_state("task_B", caller_id="actor://maxx", new_state=TaskState.COMPLETED, result="processed")

    # Now task_C can be assigned and completed
    assignment_4 = orch.assign_next_ready_task(worker_id="worker_daxx_3")
    assert assignment_4["task_id"] == "task_C"
    orch.transition_state("task_C", caller_id="actor://maxx", new_state=TaskState.COMPLETED, result="published")
    print(f"  -> Assigned and completed {assignment_4['task_id']}.")

    # 4. Replay Audit Verification
    print("\n--- WITNESS-GATE: REPLAY AUDIT OF BUSY TASK RUN ---")
    audit_res = orch.replay_audit()
    print(json.dumps(audit_res, indent=2))
    assert audit_res["audit_verdict"] == "VERIFIED_TASK_DEPENDENCY_INVARIANCE"
    assert audit_res["duplicate_claims"] == 0
    assert audit_res["out_of_order_errors"] == 0

    receipt = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "orchestrator_authority": "actor://maxx",
        "judge_gate_single_authority": True,
        "worker_claim_rejections": 1,
        "dependency_violations_blocked": 1,
        "tasks_completed": 3,
        "audit_replay_events": audit_res["total_ledger_events"],
        "duplicate_claims": audit_res["duplicate_claims"],
        "out_of_order_errors": audit_res["out_of_order_errors"],
        "verdict": "VERIFIED_GOVERNED_TASK_ORCHESTRATION",
        "ledger_file": LEDGER_TEST_PATH
    }

    with open(RECEIPT_PATH, "w") as f:
        json.dump(receipt, f, indent=2)

    print(f"\n[RECEIPT COMMITTED] -> {RECEIPT_PATH}")

if __name__ == "__main__":
    main()
