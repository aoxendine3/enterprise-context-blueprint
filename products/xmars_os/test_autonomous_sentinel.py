import os
import sys
from autonomous_sentinel import autonomous_monitor

ssot = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
files = [
    os.path.join(ssot, "products", "xmars_os", "server.py"),
    os.path.join(ssot, "products", "xmars_os", "autonomous_sentinel.py")
]

print("--- STEP 1: CAPTURE IMMUTABLE BASELINE SNAPSHOT ---")
snap = autonomous_monitor.capture_snapshot("live_baseline_v1", files)
print(f"Snapshot ID: {snap['snapshot_id']}")
print(f"Merkle Root: {snap['merkle_root']}")

print("\n--- STEP 2: TEST SUCCESSFUL UPGRADE PASS ---")
receipt_pass = autonomous_monitor.apply_verified_upgrade(
    upgrade_id="sentinel_self_test_v1",
    files_to_modify=files,
    flame_test_cmd="python -c \"print('FLAME TEST OK')\"",
    upgrade_fn=lambda: None
)
print(f"Status: {receipt_pass['status']}")
print(f"Flame Test Passed: {receipt_pass.get('flame_test_passed')}")

print("\n--- STEP 3: TEST FAILED UPGRADE AND ATOMIC ROLLBACK ---")
receipt_fail = autonomous_monitor.apply_verified_upgrade(
    upgrade_id="synthetic_failure_simulation",
    files_to_modify=files,
    flame_test_cmd="python -c \"import sys; sys.exit(1)\"",
    upgrade_fn=lambda: None
)
print(f"Status: {receipt_fail['status']}")
print(f"Rollback Verified Match: {receipt_fail.get('rollback', {}).get('verified_merkle_match')}")
print(f"Rollback Latency: {receipt_fail.get('rollback', {}).get('rollback_latency_ms')} ms")

print("\n--- STEP 4: FINAL SENTINEL AUDIT ---")
status = autonomous_monitor.get_status()
print(f"Total Snapshots: {status['total_snapshots']}")
print(f"Rollbacks Executed: {status['rollbacks_executed']}")
print(f"Verified Upgrades: {status['active_upgrades_verified']}")
