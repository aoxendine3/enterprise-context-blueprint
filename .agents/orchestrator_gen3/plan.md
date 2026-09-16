# Orchestration Plan — Milestone M1 Remediation & Gate Certification

## Objective
Remediate the CLI `--json` subparser inheritance defect in `workspaces/demo_app/demo_app/cli.py`, verify 66/66 tests pass, dispatch Phase 2 verification specialists (2 Reviewers, 2 Challengers, 1 Forensic Auditor), achieve Gate PASS, and report completion to the Sentinel.

## Phase 1: Remediation Worker Dispatch & Execution
1. Dispatch `teamwork_preview_worker_m1_2` to:
   - Modify `workspaces/demo_app/demo_app/cli.py` so `--json` is registered both at the root level and on all subparsers (`greet`, `status`, `calc`), e.g., via a shared `common_parser` parent or direct argument addition.
   - Run `python workspaces/demo_app/tests/run_tests.py` and ensure 66/66 tests pass (including `test_e2e_subcommand_status_json`).
   - Run manual verification invocations:
     - `python workspaces/demo_app/main.py status --system --json`
     - `python workspaces/demo_app/main.py greet --name "Alice" --json`
     - `python workspaces/demo_app/main.py calc --calc "1,2,3" --json`
   - Produce a detailed handoff report in `.agents/teamwork_preview_worker_m1_2/handoff.md`.

## Phase 2: Independent Specialist Verification
1. Dispatch Reviewer 1 (`teamwork_preview_reviewer_m1_1_gen3`):
   - Review code quality, syntax compliance, and run the test suite.
2. Dispatch Reviewer 2 (`teamwork_preview_reviewer_m1_2_gen3`):
   - Review robustness, edge cases, error handling, exit codes, and run the test suite.
3. Dispatch Challenger 1 (`teamwork_preview_challenger_m1_1_gen3`):
   - Invariant testing, property-based checks, and mathematical algorithmic stress testing.
4. Dispatch Challenger 2 (`teamwork_preview_challenger_m1_2_gen3`):
   - Adversarial CLI fuzzing, exit code validation, and error stream separation.
5. Dispatch Forensic Auditor (`teamwork_preview_auditor_m1_1_gen3`):
   - Full integrity verification (authenticity, no cheating, dynamic test validation, live execution checks).

## Phase 3: Gate Evaluation & Sentinel Notification
1. Read each specialist's `handoff.md` and populate `GATE_STATUS.md`.
2. Evaluate Gate Pass Criteria:
   - 66/66 tests pass.
   - All Reviewers APPROVE.
   - All Challengers confirm correctness.
   - Forensic Auditor is CLEAN.
3. Upon Gate PASS:
   - Update `progress.md` and `PROJECT.md` (Milestone M1 status -> DONE).
   - Write final orchestrator `handoff.md`.
   - Send completion message to Sentinel (`7b15f4d1-0026-419a-84b0-740caf19f8f9`).
