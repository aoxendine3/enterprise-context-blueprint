# Persona Security Hardening Blueprint (Implementation-Ready)

Source basis: completed audit in agent `75f06cc0-2203-4eaf-9288-0a005c484bf6`.

Scope in this document:
- wake controller gating/idempotence
- persona-memory bridge contract repair
- persona lock override controls
- memory trust labeling/sanitization
- sentinel schema persistence fix
- path root resolver centralization
- immune-system safe mode

Constraints:
- No runtime code edits in this pass (blueprint only).
- Plan is designed to run in parallel with ongoing filesystem reorg with minimal merge conflict.

---

## 1) File-by-File Patch Blueprint

## A. Wake Controller Gating and Idempotence

### File: `AI_Core/Xoras_Project/xoras-core/Source/xoras_wake_controller.py` (new)
- Add class: `WakeController`
- Add dataclasses: `WakePhaseResult`, `WakeStatus`
- Add methods:
  - `acquire_startup_lock()`
  - `release_startup_lock()`
  - `run_phase(name, check_fn, retries=3, backoff_s=1.0)`
  - `run_startup_contract()`
  - `is_idempotent_startup()`
- Preconditions:
  - `XORAS_ROOT` can be resolved.
  - lockfile location writable.
  - health check callables for persona bridge, sentinel, memory, daemon are injectable.
- Invariants:
  - only one startup can run at a time per root.
  - no "startup complete" status unless all required phases pass.
  - repeated startup call with healthy services is a no-op.
- Must-pass tests:
  - `test_startup_fails_when_persona_bridge_unhealthy`
  - `test_startup_retries_and_backoff_then_fails`
  - `test_startup_idempotent_with_existing_lock_and_healthy_pids`
  - `test_startup_releases_lock_on_exception`
- Rollback:
  - feature flag `XORAS_WAKE_CONTROLLER_ENABLED=0` reverts to legacy startup path.
  - keep old startup function path for one release cycle.

### File: `AI_Core/Xoras_Project/xoras-core/Source/xoras_startup.py` (modify)
- Modify or add functions:
  - `main()` (or current startup entrypoint): delegate to `WakeController.run_startup_contract()`
  - `emit_startup_summary(status: WakeStatus)`
  - `legacy_startup_path()` retained behind feature flag
- Preconditions:
  - `WakeController` importable.
  - existing startup phases can be represented as discrete checks.
- Invariants:
  - do not log success on partial health.
  - startup exit code is non-zero on failed required phase.
- Must-pass tests:
  - `test_startup_exits_nonzero_on_failed_required_phase`
  - `test_startup_logs_phase_results_deterministically`
- Rollback:
  - switch flag to legacy path.
  - if required, revert this file only; new controller file remains inert.

### File: `AI_Core/Xoras_Project/xoras-core/Source/xoras_daemon.py` (modify)
- Modify or add functions:
  - `get_daemon_readiness()`
  - `write_daemon_pidfile()` hardening
  - `is_duplicate_daemon_instance()`
- Preconditions:
  - PID file path stable and root-resolved.
- Invariants:
  - daemon boot cannot create duplicate active process for same service key.
- Must-pass tests:
  - `test_duplicate_daemon_spawn_blocked`
  - `test_daemon_readiness_health_endpoint_stable`
- Rollback:
  - disable strict duplicate check via `XORAS_DAEMON_DEDUPE_STRICT=0`.

---

## B. Persona-Memory Bridge Contract Repair

### File: `AI_Core/Xoras_Project/xoras-core/Source/xoras_memory_bridge_contract.py` (new)
- Add protocol/interface:
  - `class PersonaMemoryBridgeContract(Protocol):`
    - `enrich_chat(conversation_id, user_input, context)`
    - `persist_turn(conversation_id, user_input, response, persona_name, trust_level)`
    - `index_dream_insight(insight, tags, source)`
- Add validator:
  - `assert_persona_bridge_contract(bridge_obj)`
- Preconditions:
  - typing/protocol support available.
- Invariants:
  - persona API only depends on this contract, not concrete bridge internals.
- Must-pass tests:
  - `test_bridge_contract_validation_passes_for_persona_bridge`
  - `test_bridge_contract_validation_fails_for_l2_bridge`
- Rollback:
  - fallback import alias points to legacy bridge module.

### File: `AI_Core/Xoras_Project/xoras-core/Source/xoras_memory_bridge_persona.py` (new)
- Add class: `PersonaMemoryBridge`
- Add singleton accessor: `get_persona_memory_bridge()`
- Implement all contract methods.
- Preconditions:
  - storage backend available or safe no-op mode for degraded startup.
- Invariants:
  - methods return schema-consistent dicts.
  - no exception escapes that forces persona fallback without explicit error code.
- Must-pass tests:
  - `test_enrich_chat_returns_contract_shape`
  - `test_persist_turn_handles_storage_errors_without_crash`
- Rollback:
  - point accessor to compatibility wrapper over current module.

### File: `AI_Core/Xoras_Project/xoras-core/Source/xoras_memory_bridge.py` (modify)
- Keep as compatibility shim only:
  - export explicit aliases `get_l2_memory_bridge()` and `get_persona_memory_bridge()`; remove ambiguous `get_memory_bridge()`.
- Preconditions:
  - both concrete bridges import safely.
- Invariants:
  - no API ambiguity for callers.
- Must-pass tests:
  - `test_memory_bridge_shim_exports_expected_accessors`
- Rollback:
  - restore previous accessor while keeping warning logs.

### File: `AI_Core/Xoras_Project/xoras-core/Source/xoras_persona_api.py` (modify)
- Modify symbols:
  - import `get_persona_memory_bridge`
  - call `assert_persona_bridge_contract` at startup and first request path
  - add guarded error response `persona_memory_bridge_contract_error`
- Preconditions:
  - new contract module exists.
- Invariants:
  - persona compose endpoint never silently downgrades to generic persona on bridge mismatch.
- Must-pass tests:
  - `test_persona_api_rejects_invalid_bridge_contract`
  - `test_persona_api_returns_explicit_error_not_generic_fallback`
- Rollback:
  - feature flag `XORAS_PERSONA_BRIDGE_CONTRACT_STRICT=0` to retain old behavior for emergency.

---

## C. Persona Lock Override Controls

### File: `AI_Core/Xoras_Project/xoras-core/Source/xoras_persona_engine.py` (modify)
- Add enums/constants:
  - `PersonaLockMode = {"fixed", "allowlisted", "free"}`
- Add/modify functions:
  - `resolve_persona_override(request_ctx, parsed_user_text)`
  - `validate_override_authority(request_ctx, override_request)`
  - `enforce_persona_lock(agent_identity, lock_mode, override_request)`
- Preconditions:
  - session context carries `agent_identity`, `lock_mode`, and source metadata.
- Invariants:
  - `fixed`: no override accepted.
  - `allowlisted`: only trusted source+token accepted.
  - `free`: existing behavior permitted.
  - inline user text cannot override when lock is not `free`.
- Must-pass tests:
  - `test_fixed_mode_blocks_inline_override`
  - `test_allowlisted_mode_requires_trusted_source_and_token`
  - `test_free_mode_preserves_explicit_override_behavior`
- Rollback:
  - set default `lock_mode=free` and disable authority checks with feature flag.

### File: `AI_Core/Xoras_Project/xoras-core/Source/xoras_persona_api.py` (modify)
- Add request contract fields:
  - `override_source`
  - `override_token`
  - `requested_persona`
- Add function:
  - `parse_override_control_headers_or_payload()`
- Preconditions:
  - API contract update versioned (backward-compatible defaults).
- Invariants:
  - untrusted clients cannot mutate locked persona state.
- Must-pass tests:
  - `test_override_fields_ignored_without_trusted_source`
  - `test_override_audit_log_written_on_attempt`
- Rollback:
  - keep old payload schema accepted under `api_version=v1`.

### File: `AI_Core/Xoras_Project/xoras-core/xoras-config/personas/registry.yaml` (modify)
- Add fields per persona or per agent binding:
  - `lock_mode`
  - `override_allowlist`
  - `default_persona_binding`
- Preconditions:
  - schema reader tolerates missing fields with secure defaults.
- Invariants:
  - missing `lock_mode` defaults to `fixed` for protected agents.
- Must-pass tests:
  - `test_registry_defaults_secure_lock_mode`
  - `test_registry_rejects_invalid_lock_mode_value`
- Rollback:
  - rollback to previous schema with migration adapter mapping to `free`.

---

## D. Memory Trust Labeling and Sanitization

### File: `AI_Core/Xoras_Project/xoras-core/Source/xoras_memory_core.py` (modify)
- Add trust model:
  - `TrustLabel = {"trusted_system", "trusted_user", "untrusted_external"}`
- Add/modify functions:
  - `write_memory(..., trust_label, source_type, source_id)`
  - `sanitize_memory_payload(memory_text, trust_label)`
  - `is_imperative_injection_pattern(text)`
- Preconditions:
  - all memory write paths pass source metadata.
- Invariants:
  - every memory record has non-null trust label.
  - untrusted content cannot be emitted raw into system-context prompt.
- Must-pass tests:
  - `test_memory_write_requires_trust_label`
  - `test_untrusted_memory_imperatives_are_sanitized`
  - `test_trusted_system_memory_not_over_sanitized`
- Rollback:
  - set `XORAS_MEMORY_TRUST_ENFORCE=0` to treat missing labels as `trusted_user` temporarily.

### File: `AI_Core/Xoras_Project/xoras-core/Source/xoras_vector_db.py` (modify)
- Modify ingestion/query functions:
  - persist `trust_label`, `ingest_source`, `ingest_timestamp`.
  - filter retrieval by minimum trust threshold for prompt composition context.
- Preconditions:
  - vector metadata schema supports additional fields.
- Invariants:
  - retrieval path never returns unlabeled memory to composer.
- Must-pass tests:
  - `test_vector_ingest_persists_trust_metadata`
  - `test_prompt_retrieval_excludes_unlabeled_or_untrusted_when_required`
- Rollback:
  - metadata fields remain optional but warning-logged.

### File: `AI_Core/Xoras_Project/xoras-core/Source/xoras_sovereign_ai.py` (modify)
- Add/modify functions:
  - `compose_prompt_with_trust_boundary(...)`
  - `sanitize_recalled_memories_before_prompt(...)`
- Preconditions:
  - retrieval now provides trust metadata.
- Invariants:
  - no recalled memory can emit role directives into final system/agent instructions.
- Must-pass tests:
  - `test_prompt_builder_strips_role_claims_from_untrusted_memory`
  - `test_prompt_builder_preserves_semantic_facts_after_sanitization`
- Rollback:
  - fallback to old composer with high-severity warning telemetry.

### File: `AI_Core/Xoras_Project/xoras-core/Source/xoras_meta_orchestrator.py` (modify)
- Modify memory handoff functions:
  - enforce trust labeling on any external/tool-origin memories.
  - add explicit boundary marker in orchestration payload.
- Preconditions:
  - downstream components accept trust marker.
- Invariants:
  - tool output and external documents are never implicitly trusted as system.
- Must-pass tests:
  - `test_meta_orchestrator_marks_tool_output_untrusted_external`
  - `test_boundary_marker_propagates_to_prompt_composer`
- Rollback:
  - disable strict handoff rejection, retain warning logs.

### File: `AI_Core/Xoras_Project/xoras-core/Source/xoras_langgraph_engine.py` (modify)
- Modify conversation identity:
  - replace static `conversation_id="langgraph"` with deterministic `agent_id:session_id`.
- Preconditions:
  - caller context exposes stable `agent_id` and `session_id`.
- Invariants:
  - no cross-session memory bleed.
- Must-pass tests:
  - `test_conversation_ids_unique_per_session`
  - `test_no_cross_session_memory_recall`
- Rollback:
  - compatibility mode maps missing IDs to legacy value only in offline/dev mode.

---

## E. Sentinel Schema Persistence Fix

### File: `AI_Core/Xoras_Project/xoras-core/Source/xoras_response_sentinel.py` (modify)
- Modify/add symbols:
  - `SENTINEL_SCHEMA_VERSION = 2`
  - `ensure_schema_v2(conn)`
  - `migrate_schema_v1_to_v2(conn)`
  - `insert_sentinel_event(event)` with canonical column names
  - `verify_persistence_round_trip(conn)` startup self-test
- Preconditions:
  - sqlite/db access at startup.
- Invariants:
  - insert columns and table schema are 1:1 aligned.
  - failed writes surface as health failure, not silent pass.
- Must-pass tests:
  - `test_schema_migration_v1_to_v2_preserves_events`
  - `test_insert_and_query_round_trip_succeeds`
  - `test_startup_health_fails_when_sentinel_write_fails`
- Rollback:
  - schema migration is additive/backward-compatible; keep backup table `sentinel_events_v1_backup`.
  - emergency fallback to read-only mode with explicit degraded status.

---

## F. Path Root Resolver Centralization

### File: `AI_Core/Xoras_Project/xoras-core/Source/xoras_paths.py` (new)
- Add symbols:
  - `resolve_xoras_root()`
  - `resolve_path(*parts)`
  - `assert_path_under_root(path)`
  - cached config object `XorasPaths`
- Preconditions:
  - env var `XORAS_ROOT` optional, canonical fallback discoverable.
- Invariants:
  - no runtime-critical file path is hardcoded to user-specific absolute root.
  - all resolved paths remain under root boundary.
- Must-pass tests:
  - `test_resolve_root_prefers_env_then_auto_detect`
  - `test_assert_path_under_root_blocks_escape`
  - `test_known_runtime_paths_resolve_after_reorg`
- Rollback:
  - allow legacy absolute path fallback for one release (`XORAS_PATH_LEGACY_FALLBACK=1`).

### File: `AI_Core/Xoras_Project/xoras-core/Source/xoras_system_scanner.py` (modify)
- Replace inline path literals with `resolve_path`.
- Preconditions:
  - `xoras_paths.py` available.
- Invariants:
  - scanner targets active repo root only.
- Must-pass tests:
  - `test_system_scanner_uses_resolved_root_paths`
- Rollback:
  - controlled fallback to previous root constant.

### File: `AI_Core/Xoras_Project/xoras-core/Source/xoras_daemon.py` (modify)
- Replace hardcoded roots with resolver usage.
- Preconditions:
  - path resolver imported.
- Invariants:
  - PID/log/config files remain under canonical root.
- Must-pass tests:
  - `test_daemon_paths_rooted_in_resolver_root`
- Rollback:
  - temporary env override `XORAS_DAEMON_ROOT`.

### File: `AI_Core/Xoras_Project/xoras-core/Source/xoras_sequencer.py` (modify)
- Replace root literals and compose paths via resolver.
- Preconditions:
  - no direct `Path("/Users/...")` remains.
- Invariants:
  - sequencer survives repo relocation.
- Must-pass tests:
  - `test_sequencer_path_resolution_on_moved_workspace`
- Rollback:
  - fallback to previous root constant with deprecation warning.

### File: `AI_Core/Xoras_Project/xoras-core/.agents/hooks.json` (modify)
- Update hook script paths to resolver-aware wrappers.
- Preconditions:
  - wrapper script path exists.
- Invariants:
  - hooks continue to execute post-reorg.
- Must-pass tests:
  - `test_hooks_json_paths_valid_from_new_root`
- Rollback:
  - retain backup hooks config and auto-restore script.

### File: `AI_Core/Xoras_Project/xoras-core/scripts/start_safety_hooks.sh` (modify)
- Replace hardcoded paths with `XORAS_ROOT` + resolver helper.
- Preconditions:
  - shell script can source resolver env file.
- Invariants:
  - no user-home-specific absolute path.
- Must-pass tests:
  - `test_start_safety_hooks_works_with_custom_xoras_root`
- Rollback:
  - preserve previous script as `start_safety_hooks.legacy.sh`.

### File: `AI_Core/Xoras_Project/xoras-core/watchdog.sh` (modify)
- Same path resolver adoption as hooks script.
- Must-pass tests:
  - `test_watchdog_uses_root_env_or_detected_root`
- Rollback:
  - keep `watchdog.legacy.sh` callable.

### File: `AI_Core/Xoras_Project/xoras-core/XORAS_MASTER_AGENT_REGISTRY.md` (modify)
- Update documentation references to resolver-based root assumptions.
- Must-pass tests:
  - docs consistency check (link/path validation job)
- Rollback:
  - docs-only revert.

---

## G. Immune-System Safe Mode

### File: `AI_Core/Xoras_Project/xoras-core/Source/xoras_immune_system.py` (modify)
- Add mode controls:
  - `IMMUNE_SAFE_MODE = {"propose_only", "apply_with_approval", "disabled"}`
- Add/modify functions:
  - `generate_patch_proposal(error_ctx)` (no write)
  - `request_patch_approval(proposal)`
  - `apply_patch_with_policy_gate(proposal)` (only if explicitly approved)
  - remove or gate any direct file overwrite path behind approval+policy checks.
- Preconditions:
  - policy engine and approval channel available.
- Invariants:
  - no autonomous write to runtime source in `propose_only`.
  - all applied patches produce signed audit event.
- Must-pass tests:
  - `test_propose_only_never_writes_files`
  - `test_apply_requires_explicit_approval_token`
  - `test_patch_attempt_logged_with_hash_and_actor`
- Rollback:
  - set `IMMUNE_SAFE_MODE=disabled` to bypass self-heal subsystem entirely.

### File: `AI_Core/Xoras_Project/xoras-core/Source/xoras_triplet_nexus.py` (modify)
- Add policy entrypoint:
  - `validate_patch_ast_and_policy(proposal, target_file)`
  - protected-file denylist enforcement.
- Preconditions:
  - immune system routes apply requests through this gate.
- Invariants:
  - protected files cannot be modified by auto-heal path.
- Must-pass tests:
  - `test_protected_files_rejected_by_policy_gate`
  - `test_ast_policy_rejects_dynamic_exec_in_patch`
- Rollback:
  - keep validator passive (warn-only) in emergency mode for one release.

---

## 2) Pre-Merge Contract Test Suite (Required Gates)

Add test package: `AI_Core/Xoras_Project/xoras-core/Source/tests/contracts/`

Required test files:
- `test_wake_controller_contract.py`
- `test_persona_bridge_contract.py`
- `test_persona_lock_controls.py`
- `test_memory_trust_boundaries.py`
- `test_sentinel_persistence.py`
- `test_path_resolution_contract.py`
- `test_immune_safe_mode.py`

Merge gate policy:
- All contract tests green.
- No fallback-to-generic-persona path without explicit error.
- No startup success log when any required service check fails.
- No unlabeled memory allowed into prompt composition path.
- No autonomous source overwrite in immune safe mode default.

---

## 3) Phased Implementation Schedule (Reorg-Compatible, Minimal Conflict)

### Phase 0 - Branch/Flag Preparation (Day 0)
- Create `hardening/contract-first` branch from current integration branch.
- Introduce feature flags only (no behavior flips yet).
- Land tests skeleton and failing contract assertions.
- Conflict minimization: additive files only; avoid path rewrites in this phase.

### Phase 1 - Additive Foundations (Days 1-2)
- Add new files only:
  - `xoras_wake_controller.py`
  - `xoras_memory_bridge_contract.py`
  - `xoras_memory_bridge_persona.py`
  - `xoras_paths.py`
- Add contract tests for each new module.
- Conflict minimization: no existing file moves; no shell script edits yet.

### Phase 2 - Controlled Integrations Behind Flags (Days 2-4)
- Wire startup to wake controller in `xoras_startup.py`.
- Wire persona API to explicit bridge contract in `xoras_persona_api.py`.
- Add persona lock enforcement in `xoras_persona_engine.py` with permissive default for rollout.
- Conflict minimization: limit each PR to one subsystem + tests.

### Phase 3 - Trust and Persistence Hardening (Days 4-6)
- Implement trust labeling/sanitization across memory and composer files.
- Fix sentinel schema and migration in `xoras_response_sentinel.py`.
- Enable strict assertions in staging only.
- Conflict minimization: avoid touching reorg-moved files until paths stabilize.

### Phase 4 - Path Centralization Sweep (Days 6-8)
- Migrate root/path usage to `xoras_paths.py` incrementally:
  - python modules first
  - shell scripts and hooks second
  - docs last
- Conflict minimization: sequence PRs by directory ownership used by reorg worker.

### Phase 5 - Immune Safe Mode Enforcement (Days 8-9)
- Switch immune system default to `propose_only`.
- Gate any apply path via approval+policy in triplet nexus.
- Conflict minimization: isolated PR focused on immune subsystem.

### Phase 6 - Production Rollout and Cleanup (Days 10+)
- Flip strict flags gradually:
  - staging -> canary -> full
- Remove temporary legacy fallbacks after 1-2 release cycles.
- Finalize docs and run post-rollout audit replay.

---

## 4) Rollback Playbook (Global)

- Keep all major behavior flips behind flags for fast rollback.
- Rollback order (if incident):
  1. disable strict memory trust enforcement
  2. disable wake controller strict gating
  3. disable persona override strictness
  4. disable immune apply path entirely
- Preserve telemetry in degraded mode; never disable sentinel logging silently.
- Maintain compatibility shims for bridge and path resolver for one release cycle minimum.

---

## 5) Blockers and Dependencies

No hard blocker for blueprint creation.

Execution dependencies before implementation starts:
- Confirm canonical runtime root expected by reorg stream (`XORAS_ROOT` convention).
- Confirm authoritative session identity fields (`agent_id`, `session_id`) available everywhere persona/memory is called.
- Confirm production policy for immune subsystem approval channel (human, signed token, or CI gate).
- Confirm schema migration window for sentinel DB (downtime-free vs maintenance window).

---

## 6) Suggested PR Breakdown (Small, Reviewable)

- PR1: contract tests + additive interfaces (`wake controller`, `bridge contract`, `paths`)
- PR2: startup gating/idempotence wiring
- PR3: persona lock controls + registry schema
- PR4: memory trust labels + sanitization enforcement
- PR5: sentinel schema migration + health self-test
- PR6: path centralization sweep
- PR7: immune safe mode and policy gate

Each PR should include:
- feature flags defaults
- backward compatibility note
- explicit rollback command/env toggle
- required contract tests for touched subsystem
