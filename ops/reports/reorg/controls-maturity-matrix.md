# Controls Maturity Matrix

Date: 2026-07-04  
Scope: Sovereign stack technical review findings, persona lock/security hardening blueprint, and reorg/governance artifacts in `Xoras_Workspace`.

## Evidence Sources Used

- `/Users/ajoxendine68/.cursor/projects/Users-ajoxendine68-Desktop-Xoras-Workspace/agent-transcripts/9be8c075-0fed-406c-a879-400dfb6c7465/9be8c075-0fed-406c-a879-400dfb6c7465.jsonl`
- `/Users/ajoxendine68/Desktop/Xoras_Workspace/ops/reports/reorg/persona-security-hardening-blueprint.md`
- `/Users/ajoxendine68/Desktop/Xoras_Workspace/ops/reports/reorg/verification-phase5-highrisk.md`
- `/Users/ajoxendine68/Desktop/Xoras_Workspace/ROOTS.md`
- `/Users/ajoxendine68/Desktop/Xoras_Workspace/LEGACY_REDIRECTS.md`
- `/Users/ajoxendine68/Desktop/Xoras_Workspace/AI_Core/Xoras_Project/xoras-core/Docs/honest_engineering_audit.md`
- `/Users/ajoxendine68/Desktop/Xoras_Workspace/AI_Core/Xoras_Project/xoras-core/TEST_INFRA.md`
- `/Users/ajoxendine68/Desktop/Xoras_Workspace/AI_Core/Xoras_Project/xoras-core/Docs/meta_swarm_report_18c8dc.md`
- `/Users/ajoxendine68/Desktop/Xoras_Workspace/AI_Core/Xoras_Project/xoras-core/Docs/omni_dojo_audit.md`

## Scoring Model

- 1 = ad hoc / mostly undocumented
- 2 = partial controls, inconsistent enforcement
- 3 = defined controls, moderate enforcement
- 4 = strong enforcement, measured and repeatable
- 5 = optimized, continuously verified, production-grade

Current weighted posture (simple average): **1.8 / 5**  
Target posture (next 90 days): **3.9 / 5**

---

## Executive Decision View

### Top 5 Systemic Risks

1. **Determinism risk at startup/wake:** required startup phases are not yet strictly gated and idempotent.
2. **Identity and override risk:** persona lock and override authority are not uniformly enforced.
3. **Evidence risk:** scale/reliability claims exceed reproducible proof quality and CI-backed artifacts.
4. **Path/config drift risk:** legacy absolute paths and deferred redirects create deployment and rollback fragility.
5. **Injection/boundary risk:** trust labeling and sanitization boundaries are designed but not uniformly implemented.

### Top 5 Leverage Improvements

1. **Ship contract test gates first** (wake, persona lock, trust boundaries, sentinel persistence, path resolution).
2. **Enforce strict startup/wake controller** with idempotence and non-zero exit on required phase failure.
3. **Centralize path resolution** (`XORAS_ROOT` contract) and remove hardcoded roots from runtime-critical paths.
4. **Upgrade evidence pipeline** to deterministic, CI-enforced, artifact-producing stress/chaos suites.
5. **Default immune/self-heal to propose-only** with explicit approval and policy gate for writes.

### Ship Readiness Gate Criteria

| Gate Area | Pilot Readiness (must pass) | Production Readiness (must pass) |
|---|---|---|
| Identity & Persona | Persona lock modes implemented for protected agents; override attempts audited | Signed/authorized override flow only; no inline override on locked personas |
| Wake/Bootstrap | Deterministic startup contract in place with phase status output | Idempotent startup + fail-safe rollback + repeated clean cold/warm starts |
| Injection/Memory Trust | Trust labels present on new memory writes and prompt sanitization active | Full trust-label coverage, retrieval threshold enforcement, zero unlabeled prompt memory |
| Orchestration/Isolation | Delegation boundaries and worker constraints documented and tested at moderate scale | Formal policy controls + failure containment SLOs validated in chaos tests |
| WAL/Recovery | WAL/state integrity checks pass in staged fault tests | Recovery RTO/RPO targets met under repeatable kill/corruption scenarios |
| Observability/Audit | Structured logs and event schemas for critical controls | End-to-end traceability with retention, alerting, and compliance-ready audit exports |
| Test Evidence | Reproducible test runner and baseline artifacts generated | CI-enforced regression + stress/chaos matrix with signed release evidence |
| Deployment Hygiene | Canonical root and redirect governance enforced for pilot paths | No runtime-critical legacy path dependencies; verified rollback scripts per batch |
| Cost/Capacity | Baseline latency/capacity telemetry and thresholds defined | Capacity budgets, quota controls, and cost/perf SLO alarms continuously enforced |

---

## Priority-Ordered Controls Matrix

| Priority | Control Domain | Current | Target | Evidence (specific paths) | Key Gaps | High-Priority Fixes | Owner | 30-Day Milestone | 60-Day Milestone | 90-Day Milestone |
|---|---|---:|---:|---|---|---|---|---|---|---|
| P0 | Wake/Bootstrap Determinism | 1 | 4 | `ops/reports/reorg/persona-security-hardening-blueprint.md`, `ROOTS.md`, `agent-transcripts/...9be8...jsonl` | Required phases not hard-gated; startup success can be non-deterministic; idempotence missing | Implement `WakeController`, locking, deterministic phase checks, and strict exit behavior behind feature flags | Runtime | Wake contract tests added and failing-to-pass baseline established | Staging rollout with deterministic startup logs and lock semantics | Default strict wake mode enabled with rollback flag retained |
| P0 | Identity & Persona Governance | 2 | 4 | `ops/reports/reorg/persona-security-hardening-blueprint.md`, `ROOTS.md` | Persona override authority and lock-mode controls are not consistently enforced | Enforce `fixed/allowlisted/free`, trusted-source override contract, registry schema hardening, audit on attempts | Security + App | Lock-mode schema and API fields landed with compatibility path | Protected agents enforced in staging, with negative tests green | Strict policy default for protected agents in production path |
| P0 | Prompt/Memory Injection Defense | 2 | 4 | `ops/reports/reorg/persona-security-hardening-blueprint.md`, `ROOTS.md`, `agent-transcripts/...9be8...jsonl` | Trust labeling incomplete; untrusted memory sanitization and retrieval thresholds not universal | Add trust labels everywhere, sanitize imperative/role-claim patterns, enforce trusted retrieval thresholds | App + Security | Trust metadata schema and sanitizer tests shipped | Prompt composition trust boundary fully wired in staging | Zero-unlabeled-memory gate enabled for production |
| P0 | Test Evidence Quality / Reproducibility | 1 | 4 | `AI_Core/Xoras_Project/xoras-core/TEST_INFRA.md`, `AI_Core/.../Docs/meta_swarm_report_18c8dc.md`, `agent-transcripts/...9be8...jsonl` | Test artifacts are not consistently proof-grade; CI/harness evidence quality gaps | Standardize deterministic runner, seeds, environment metadata, JUnit/perf artifacts, and release evidence checklist | Runtime + Ops | Unified reproducible runner and artifact schema published | Stress/chaos/regression matrix running in CI for pilot targets | Signed, repeatable evidence package required for production releases |
| P1 | Deployment & Path Configuration Hygiene | 2 | 4 | `ROOTS.md`, `LEGACY_REDIRECTS.md`, `ops/reports/reorg/verification-phase5-highrisk.md`, `agent-transcripts/...9be8...jsonl` | Legacy hardcoded paths and deferred redirects create runtime and launcher fragility | Centralize path resolver, remove hardcoded roots, execute segmented migration batches with rollback evidence | Ops + Runtime | Path inventory and resolver contract tests complete | High-risk batch migrations executed with smoke checks and rollback drills | Legacy runtime path dependencies reduced to zero for core services |
| P1 | Orchestration & Delegation Controls | 2 | 4 | `AI_Core/.../Docs/meta_swarm_report_18c8dc.md`, `agent-transcripts/...9be8...jsonl`, `ROOTS.md` | Coordination model present but policy-grade delegation constraints are weak; simulation-heavy evidence | Define delegation contracts, bounded authorities, and failure containment tests at real process scale | App + Runtime | Delegation policy contract documented and test skeleton added | Real-process scale tests for selected workloads executed | Policy-enforced delegation and containment SLOs validated |
| P1 | Runtime Isolation / Sandbox | 2 | 4 | `agent-transcripts/...9be8...jsonl`, `ops/reports/reorg/persona-security-hardening-blueprint.md` | Isolation exists but bypass surface and policy enforcement depth are insufficient for production claims | Tighten allowed runtime surface, enforce policy gate for dynamic execution and self-heal writes | Security + Runtime | Red-team test corpus defined and integrated into regression | High-risk bypass classes blocked in staging | Continuous adversarial isolation tests in release gate |
| P1 | Observability & Auditability | 2 | 4 | `AI_Core/.../Docs/omni_dojo_audit.md`, `ops/reports/reorg/persona-security-hardening-blueprint.md`, `agent-transcripts/...9be8...jsonl` | Partial logs/records exist, but control-plane audit coverage and standardized telemetry are incomplete | Standardize event schema, add control-level audit events, and define retention/alerting policy | Ops + Security | Critical control events mapped to schema and log sinks | Alert thresholds + audit dashboards for pilot controls | Compliance-ready control evidence export and retention verified |
| P2 | Data Integrity / WAL / State Recovery | 3 | 4 | `agent-transcripts/...9be8...jsonl`, `ops/reports/reorg/persona-security-hardening-blueprint.md`, `AI_Core/.../Docs/omni_dojo_audit.md` | Strong primitives exist, but sentinel persistence and recovery proofs need stronger repeatable validation | Complete sentinel schema migration, round-trip verification, and fault-injection recovery suite | Runtime | Sentinel schema migration and health self-test implemented | Recovery chaos tests across kill/corruption paths pass in staging | RTO/RPO and integrity SLOs formalized and enforced |
| P2 | Cost/Capacity/Performance Controls | 1 | 3 | `AI_Core/.../Docs/honest_engineering_audit.md`, `agent-transcripts/...9be8...jsonl`, `ops/reports/reorg/verification-phase5-highrisk.md` | Capacity and cost guardrails are under-defined; scale/perf claims not tied to governance thresholds | Define capacity budgets, saturation alerts, and workload-tier performance gates | Ops + Runtime | Baseline perf/capacity dashboard and alert thresholds defined | Budget/quota controls added for pilot workloads | Production budget/SLO policy integrated into release approval |

---

## Decision-Ready Priority Order (Do First)

1. **P0 contract gate stack:** wake determinism, identity/persona policy, trust-boundary enforcement, reproducible tests.
2. **P1 stabilization stack:** path hygiene + orchestration policy + runtime isolation hardening + audit schema.
3. **P2 hardening stack:** WAL/recovery proof depth + cost/capacity governance integrated into release gates.

## Recommended Owners and Cadence

- **Security:** persona governance, injection defense, isolation policy, audit authority model.
- **Runtime:** wake controller, orchestration constraints, WAL/recovery, deterministic test harness.
- **Ops:** path migration checkpoints, deployment hygiene, observability pipelines, cost/capacity governance.
- **App:** persona API contracts, memory bridge trust propagation, prompt composition boundaries.

Weekly control review cadence:
- Week 1-4: close all P0 gaps.
- Week 5-8: close P1 gaps and pilot readiness gates.
- Week 9-12: close P2 and enforce production gates.

