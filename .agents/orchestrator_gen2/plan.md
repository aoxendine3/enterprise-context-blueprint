# Execution Plan — Project Orchestrator (Generation 2)

## Mission
Resume demonstration application project after predecessor network drop, dispatch Phase 2 verification specialists (Reviewers, Challengers, Forensic Auditor), evaluate gate criteria, and report completion to the Sentinel.

## Context & State Recovery
- Predecessor: `orchestrator_1` (conversation ID `38a630c1-138a-44c6-9036-bf65c9a5ad88`)
- Phase 0 (Survey & Architecture): COMPLETED by predecessor Explorers (1, 2, 3) and documented in `PROJECT.md`.
- Phase 1 (Implementation): COMPLETED by Worker (`teamwork_preview_worker_m1_1`) at `workspaces/demo_app/` with 66 passing tests (documented in `c:\Users\admin\Desktop\SSOT_Agentic_Brain\.agents\teamwork_preview_worker_m1_1\handoff.md`).
- Phase 2 (Verification): In-flight when network drop occurred; subagents terminated without delivering handoffs. Must be freshly dispatched and verified.

## Phases & Steps
1. **Step 1: Orchestrator State Initialization** [CURRENT]
   - Write `DISPATCH.md`, `BRIEFING.md`, `plan.md`, `progress.md`, and copy `PROJECT.md` to `orchestrator_gen2`.
   - Start 10-minute heartbeat cron for state liveness.

2. **Step 2: Dispatch Phase 2 Verification Specialists**
   - Create directories:
     - `.agents/teamwork_preview_reviewer_m1_1_gen2/`
     - `.agents/teamwork_preview_reviewer_m1_2_gen2/`
     - `.agents/teamwork_preview_challenger_m1_1_gen2/`
     - `.agents/teamwork_preview_challenger_m1_2_gen2/`
     - `.agents/teamwork_preview_auditor_m1_1_gen2/`
   - Dispatch 2 independent Reviewers (`teamwork_preview_reviewer`):
     - Reviewer 1: Architecture, correctness, standard stream separation, exit code discipline, unit test coverage.
     - Reviewer 2: Edge cases, boundary values, error conditions, CLI options, integration test coverage.
   - Dispatch 2 independent Challengers (`teamwork_preview_challenger`):
     - Challenger 1: Empirical verification, property-based tests, invariants, performance.
     - Challenger 2: Adversarial inputs, malformed CLI arguments, fuzzing, exception safety.
   - Dispatch 1 Forensic Auditor (`teamwork_preview_auditor`):
     - Comprehensive integrity forensics, cheating detection, checking for hardcoded outputs, dummy implementations, or bypassed checks.

3. **Step 3: Monitor & Lifecycle Management**
   - Track progress via `progress.md` updates.
   - Collect completed `handoff.md` reports from all 5 specialists.
   - Verify that all specialists provide detailed evidence and unambiguous verdicts.

4. **Step 4: Gate Evaluation**
   - Record verdicts in `GATE_STATUS.md`.
   - Verify Pass Criteria:
     1. Build and tests pass (66/66 tests pass, zero regressions).
     2. Reviewer 1 & 2 verdicts are APPROVE.
     3. Challenger 1 & 2 confirm correctness and robustness.
     4. Auditor verdict is CLEAN (zero integrity violations).

5. **Step 5: Final Completion & Reporting to Sentinel**
   - Write comprehensive `handoff.md`.
   - Send completion message to parent Sentinel (`7b15f4d1-0026-419a-84b0-740caf19f8f9`).
   - Present human-facing summary to the user.
