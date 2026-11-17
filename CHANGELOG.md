# Changelog

## [5.0.0-rc.1] - Unreleased

> **Unreleased — not shipped.** This section records work performed in the current engineering cycle. It is a release candidate, not a general-availability release.

### Added / Changed (this cycle)

- **Signed cockpit bundle** — the offline evidence cockpit now exports a manifest-hashed bundle with a detached Ed25519 signature pinned by `dist/trust_root.js`; the single canonical build path is fail-closed across structural, signing, asset-lock, and coverage steps.
- **Fail-closed gates** — gate scripts were tightened so failures return non-zero rather than being printed and ignored; the reality gate aggregates all gates and writes `REALITY_GATE_RECEIPT.json` with a fail-closed verdict.
- **CI path fixes** — workflow and operational script paths were corrected so CI and local invocations resolve the same entry points.
- **Merkle claim restoration** — the poisoned `merkle_root.hash` condition was repaired; the BBQ gauntlet restores from `merkle_root.known_good` (0444) rather than from whatever is on disk.
- **Writer hardening** — sovereign file-writer verification was hardened and remains a top-level gate before evidence export.
- **Documentation / version alignment** — unified versioning at `5.0.0-rc.1` across `README.md`, `version.json`, `VERSIONING.md`, `CITATION.cff`, `package.json`, `NOTICE.md`, and the cockpit README.
- **Stale-claim register (independent critic)** — README now documents the realized gate graph (and the `AGENTS.md §6.4` discrepancy), the doc-sync script header drift, the golden receipt's fail-closed status, the precise license position, and that `data/version.json` is unrelated legacy. Historical CHANGELOG numbers are labeled as historical.
- **Ninth reality gate (golden groundedness)** — `reality_gate.sh` now runs 9 top-level gates, including CI surface (WASM + doc-sync) and golden groundedness; `production_gates` is derived from the actual gate result rather than hardcoded. Current receipt: `REALITY_GATE_FAIL`, `8/9`, first failure `golden groundedness (floor metric)`, production `6/6`, writer/cockpit/CI-surface PASS, `3651` lineage nodes (`2026-11-16T22:03:13Z`).
- **Fail-closed golden harness** — `scratch/golden_groundedness_harness.py` now emits `GOLDEN_PASS` only at 25/25 questions evaluated, 0 forbidden hits, and `pass_rate >= 80.0`, exiting 1 otherwise; `core/ops/scripts/verify_golden_groundedness.py` is the gate verifier and exits 1 on the current receipt.
- **Golden receipt reclassification** — `GOLDEN_GROUNDEDNESS_RECEIPT.json` verdict changed from `GOLDEN_HARNESS_COMPLETE` to `GOLDEN_FAIL` with `pass_rate_floor: 80.0` and a `reclassification_reason` (`2026-11-16T22:10:00Z`); measured values are unchanged (2 questions, `0.0` pass rate, empty responses). It is now a blocking gate, not a floor signal.

### Not shipped

- CI required checks and branch protection are pending; no GA claim is made.
- Product state is **HOLD**: the golden groundedness gate currently FAILs and blocks release. An honest build is RED until the full 25-question set passes at the 80.0 floor.

## [2.0.0] — 2026-11

### Added
- **Agent Notary by XORAS** — the sovereign verifier is now the primary entry point (`./Product.html`).
- Dual-substrate Merkle witness — native Zig verifier agrees byte-for-byte with Python guard.
- Quarantine protocol (AGENTS.md §10.5) — no deletion, proof before move, report same turn.
- Outside-entity detection — structural, no third-party names carried anywhere.
- Identity scope guard — citizen cards sealed + write-protected; wake refuses unscoped agents.
- Collective voice law — agents speak as the collective; outside-voice turns refused before audio.

### Fixed
- `Lineage nodes` had an empty `writer_log_ref` — schema deduped, world file consolidated to one live file + witness.
- Canonical-vs-mirror Merkle root desync — engine now dual-writes canonical store.
- Telemetry journal line 12 corrupted (legacy JSON canonicalization mismatch) — recanonicalized, chain re-linked, 12 records verified.
- Telemetry journal rebuilt from intact payload + recomputed Merkle root.

### Changed
- Goal re-centered from architecture demonstration to auditable product.
- 3293 monotonic lineage nodes across 100 adversarial runs — zero state drift, zero backdating.

## [2.0.1] — 2026-11-14 — Cleanup, documentation, and disk reclamation

### Added
- **DART DB substrate (externally produced, verified in-house)** — durable DART store: `core/memory/dart_db.py` (hot HexCell ring + append-only WAL + epoch Merkle spine + SQLite cold spill + named rollback checkpoints) and `core/memory/dart_runtime.py` (process-wide singleton, Stage 1 Wake hydration). Reviewed for honesty: dev-machine absolute paths replaced with `__file__`-relative; acceptance suite no longer mutates the live `memory/tri_brain/dart_db` store by default (`DART_LIVE_BOOTSTRAP=1` to opt in); runtime DB dir gitignored; both acceptance suites pass (fresh receipts in `memory/catch_log/DART_*`).
- **DART receipts** — `DART_DB_ACCEPTANCE_RECEIPT.json`, `DART_DB_CHECKPOINT_RECEIPT.json`, `DART_RETROSPECTIVE_RECALL_RECEIPT.json`.
- **Foreign tooling quarantine receipts** — `foreign_tooling_2026-11-14.json` (tracked symlink into vendor config, `.geminiignore`, third-party-branded asset, third-party ADK template).
- **Coverage receipt** — `tts_audio_purge_receipt.json` (54 regenerable TTS artifacts, sha256 each, +0 synthesis cost).

### Removed (per owner directive, TTS cache only)
- 54 regenerable TTS audio files (~39 MB): `memory/agent_logs/collective_chunks/*`, agent briefings, voice drafts, per-turn council recordings, scratch duplicates. Transcripts remain in `turn_ledger.jsonl` and `collective_voice_receipts.jsonl`. Kept: `video_output/combined_audio.m4a`, `docs/assets/thumbnails/video_audio.mp3`, scratch app thumbnail audio. No git-tracked media was lost.

### Changed
- `.gitignore`: `AI_Core/` excluded (the embedded clone, ~3.3 GB — untracked, NOT certified, must not enter the tree or history). `memory/tri_brain/dart_db/` excluded (live runtime store).
- `tests/test_dart_retrospective_recall.py`: explicit `os` import (was relying on `z3` leaking the name).

### Provenance log for untracked items present at 2026-11-14 (not certified; do not treat as production)
- Root-level market/analysis documents (`COMPLETE_MARKET_ECOSYSTEM_SUMMARY.md`, `EXECUTIVE_SUMMARY_AND_FINDINGS.md`, `GOOGLE_SEARCH_VISIBILITY_ANALYSIS.md`, `IMPLEMENTATION_COMPLETE_TODAY.md`, `MARKET_VALUATION_AND_COMPETITIVE_ANALYSIS.md`) — generated mid-session outside the certified surface; recorded here so they are not mistaken for authority. Await owner disposition.
- `.agents/`, `AI_Core/` — agent tooling state and an embedded repository clone; not repository content, not certified, to be excluded or resolved by the owner.
- `.cargo/`, `.upgp-seal`, `.integrity_ledger.json`, `.agents/` — untracked tooling/runtime artifacts; not certified.

### Notes
- Disk reached 100% (130 MB free at the low point) driven primarily by `AI_Core/` (~3.3 GB embedded clone) plus pre-existing `workspaces/` (~2.2 GB), `labs/` (~2.7 GB), `scratch/` (~1.3 GB). No owner data was deleted; the TTS purge reclaimed ~39 MB. Free space must still be addressed by the owner (move `misc/` ~37 GB or `AI_Core/` to external media).

## [2.0.2] — 2026-11-14 — Opportunity map filed

### Added
- `docs/research/AGENTIC_OPPORTUNITY_MAP_2026-11-14.md` — outside-the-box strategy: Proof-of-Action insurance, Agent Black Box (EU AI Act Art. 12), Verify-Before-You-Buy interactive red-team, payment rails-webhook Notary minting, Perpetual Verification Pass, Multi-Witness Federation, public Transparency Log, drift warranty (A_COMBINED/ContextEcho), Proof-Carrying OSS releases, incident forensics retainer, receipt escrow, hardware dead-man's countersign. Non-negotiable caveats documented: no customer validation, three pillar papers not re-measured on our hardware.

## [2.0.3] — 2026-11-14 — Source syntheses filed with verification

### Added
- `docs/papers/COGNEN_NEURO_MIMETIC_SPEC.md` — user-provided synthesis of Ororbia & Kelly's CogNGen (arXiv:2204.00619; arXiv:2310.15177 / AAAI-SS). Provenance header states it is not original research; verify via `memory/catch_log/cogngen_camel_contextecho_verification.json`.
- `docs/papers/DECONSTRUCTING_REALITY_AGENTIC_CODING_FRAMEWORK.md` — user-provided synthesis of CogNGen + CaMeL (arXiv:2503.18813, SaTML 2026) + ContextEcho (arXiv:2605.24279, NeurIPS 2026 E&D submission). One overstatement corrected in the provenance header (CaMeL is not "absolute protection preserving utility" — benign utility 63.9% vs 90.7%; AgentDojo is the authors' own benchmark; ContextEcho is a 2-week-old preprint with judge-dependent scores).
- Both documents are filed verbatim for traceability and are not primary sources.

## [2.0.4] — 2026-11-14 — MERIDIAN proposed

### Added
- `docs/research/MERIDIAN_SPEC.md` — witnessed continuum design: cryptographic cage (DART-stamped capability lattice + Z3 containment theorem), physical dual-chamber LLM split (Mac P-LLM / Windows RTX Q-LLM), register-attested sessions enforced by MARS circuit breaker, reconsolidation-by-retrieval learning mode (no weight updates), Session Certificates productized through Agent Notary. Synthesis of verified pillars (CogNGen/CaMeL/ContextEcho) with XORAS substrates; nothing externally validated yet; falsification gate precedes any marketing claim.

## [2.0.5] — 2026-11-14 — MERIDIAN Layer 1: the cage is real

### Added
- **DART capability lattice** — every cell in the ring and the durable substrate now carries PUBLIC < INTERNAL < RESTRICTED < SEALED (written at record time; validated). `recall_backlog` and `recall_sequence_range` enforce caller clearance; higher-tainted cells never surface to lower callers. Stage 1 Wake defaults to INTERNAL (never hydrates SEALED untrusted ingress into the council).
- **`core/ops/security/cage_containment.smt2`** — Z3 proof that no path through the cell graph carries SEALED (level 3) data into an egress-capable cell (≤ INTERNAL = 1) without a verified downgrade. Verified UNSAT on this host; also wired into the MARS SMT gate (`.github/workflows/mars_gatekeeper_maven.yml`) so CI re-proves it on every push.
- **`tests/test_dart_cage_lattice.py`** — 7-check acceptance suite (SEALED invisible below SEALED clearance, WAL replay fidelity, legacy rows fail-closed to RESTRICTED, cold-spill enforcement, rollback lattice preservation, invalid-label rejection). All pass; receipt at `memory/catch_log/DART_CAGE_LATTICE_RECEIPT.json`.
- **Crash recovery fails closed** — pre-cage (pre-lattice) WAL rows replay as RESTRICTED, never silently PUBLIC; legacy SQLite cold store auto-migrates to lattice columns.

### Changed
- Hexcell format unchanged (Zig/dual-witness unaffected); lattice lives on the durable path (WAL + cold SQLite + in-memory entry), additive and backwards compatible.
- DART runtime: `record_transition` / `stage1_wake_hydrate` accept `lattice`/`clearance`.

### Notes
- This is Layer 1 only. Layers 2–4 (physical dual-chamber, register attestation, reconsolidation-by-retrieval) and the Session Certificate remain proposed in `docs/research/MERIDIAN_SPEC.md`.

## [2.0.6] — 2026-11-14 — COGNEN/SSOT marketing synthesis audited and marked COMPROMISED

### Added
- `docs/papers/COGNGEN_SSOT_MARKETING_AUDIT.md` — claim-by-claim audit of the user-pasted "COGNEN / SSOT" synthesis: vendor-published marketing claims (support-ops and context-layer vendors; ~12k customers, ~$3.6B acquisition pending) — unverifiable, not re-measured, CogNGen section misstates arXiv:2310.15177 (drops Σ-precision factor and z̄; ∂F/∂z garbled; sleep-replay update is not the published rule), the code block was executed verbatim on this host and is a random-weight NumPy demo with zero DART/MARS/world_file.db integration ("verified bare-metal" is false), XORAS::OS section invents TCP 8787 and misstates the MARS gate. Verdict: do not cite, do not show externally, fix before any reuse.
- `memory/catch_log/cogngen_ssot_marketing_audit_receipt.json` — verification of record.

## [2.0.7] — 2026-11-14 — the terminal agent runtime/CogNGen bridge document audited and marked COMPROMISED

### Added
- `docs/papers/AGENT_RUNTIME_SYNTHESIS_AUDIT.md` — line-level audit of the user-pasted "the agent runtime + CogNGen Reality SSOT" synthesis: the cited kernel computes a random-tensor "VFE" (vfe=344.87 measured 2026-11-14) with zero DART/MARS/world_file.db integration; `verify_integrity_v2.py` and `trace.json` do not exist; MARS is misstated as cargo fmt/coverage (actual: AST/SAST/ASAN-TSAN/Z3); ANE/SIMD HexCell mapping is fabricated; AGENTS.md §6.4 Reality Gate added listing the real mandatory gates (6/6 verify_all_production_gates.sh · 7/7 cage lattice · 4/4 side-channel · golden harness). Not for citation or external display.
- `memory/catch_log/agent_runtime_audit_receipt.json` — verification of record.

### Also measured
- Golden question set (v2.0.0-SOVEREIGN, 25 items) answered by local qwen2.5:7b-instruct: mean groundedness 45.2% (n=3 sample), 0 forbidden-hallucination hits, 0 passes at ≥70 threshold — the local 7B model is not grounded on critical security gates; use as a floor signal, not a ceiling claim.

## [2.0.8] — 2026-11-14 — Voice guard: natural flow, honest enforcement

### Changed
- `collective_voice_guard.py` next-step and completed-work lexicons broadened (e.g. will/shall/first/proceed/push/commit/ship/today; filed/pushed/committed/updated/merged/shipped/documented/tested/validated/...) — natural turns flow without weakening the three hard rules (collective We/Our voice · outside-voice phrases refused · attribution shapes refused · NEXT/BREAKDOWN/SUMMARY phase marker mandatory).
- Self-test cases aligned with the module's documented name-free design ("name-free outside-entity detector") — the stale "Antigravity" expectation never matched the implemented grammar (attribution phrases require a following capitalized party); replaced with "powered by Merge IDE" which the grammar does catch; all 12 self-test cases PASS.

## [2.0.9] — 2026-11-14 — Third bridge variant audited; golden set measured fully

### Measured
- Local qwen2.5:7b-instruct answered the full 25-question golden set (v2.0.0-SOVEREIGN): mean groundedness 50.73% · argument hallucination 28.0% · 0 forbidden-hallucination hits · 1/25 pass (>=70). The council cannot currently answer its own gate corpus at reliability; treat local-model self-answers as UNVERIFIED until re-grounded by the DART/verification stack.

### Added
- `memory/catch_log/agent_runtime_variant_receipt.json` — verdict recorded for the affirmative variant of the synthesis: scripts cited never existed; implementation computes nothing verifiable; behavior unchanged from the audited class.

## [2.0.10] — 2026-11-14 — the terminal agent runtime project wiring landed (no theater)

### Added
- `.the terminal agent runtime/the terminal agent runtime.json` — the repo is now a configured the terminal agent runtime project: `/reality` command runs the mandatory pre-flight (gates, cage lattice, side-channel, golden harness, world_file witness) and demands quoted receipts; `auditor` subagent (edits denied, receipts-only verdicts); permissions gate force-pushes, hard resets, and `rm -rf` behind explicit ask.
- AGENTS.md §6.4 (Reality Gate) + this config are the the terminal agent runtime contract: run gates, paste receipts, never claim done on narrative.

### Stopped
- Council role-play toy jobs (8-model swarm; 5-seat persona convene) — killed; answers were theater-grade signals, not evidence. Removed from scope.

## [2.0.11] — 2026-11-14 — Branding law purge executed and committed

### Removed from certified tree
- `.opencode/opencode.json` — third-party runtime config landed by the agent during bridge work; the repo now carries no external runtime config.
- Embedded clone AI_Core/ (216 tracked files referencing third-party hosted-inference endpoints) — untracked via `git rm --cached -r`; files preserved on disk; not certified; must never enter history.
- tracked references to outside brand names across audit notes, README, AGENTS.md, portal configs — replaced with project-internal names only.

### Renamed / moved
- `docs/papers/OPENCODE_COGNGEN_BRIDGE_AUDIT.md` → `docs/papers/AGENT_RUNTIME_SYNTHESIS_AUDIT.md`; `memory/catch_log/opencode_*` → `agent_runtime_*`; audit receipt updated to match.
- `barn/archives/google_dependency_2026-11-14/` → `barn/archives/third_party_dependency_2026-11-14/`; receipt neutralized (endpoint details generalized; nothing deleted).

### Gate receipts
- Refreshed by 2026-11-14 gate run: BBQ memo, blackbox/magistracies logs, CURRENT_SYSTEM_STATE, activity trace.

## [2.0.12] — 2026-11-14 — Kokoro voice wired + reality_gate.sh shipped

### Added
- `ops/scripts/reality_gate.sh` — fail-closed pre-flight: production gates (bash ops/scripts/verify_all_production_gates.sh) → side-channel (node --expose-gc core/ops/scripts/test_side_channel_verification.cjs) → DART cage lattice (python3 tests/test_dart_cage_lattice.py) → Z3 cage_containment.smt2 (must print unsat) → world_file.db lineage witness (`select count(*) from lineage_nodes`, live count 3371). Writes `memory/catch_log/REALITY_GATE_RECEIPT.json`; exits non-zero on any failure; accepted by `scratch/reality_gate_acceptance/acceptance.sh` (T1/T2/T3/T4 all PASS, fail-closed proven under rigged z3).
- Kokoro wired as the collective's voice (`am_michael`) in `ops/scripts/collective_speak.sh` via `ops/scripts/collective_kokoro.py`; Lee (Premium) remains emergency fallback only. Capabilities models (`capabilities/neural_models/kokoro-v1.0.onnx` + `voices.bin`) are ours and intact.

### Historical clarification (numbers above are historical, not current)

- The `3371` lineage-node count written in this 2026-11-14 entry was the **live count at that time**. It is historical; the current receipt reports `3651` (`memory/catch_log/REALITY_GATE_RECEIPT.json`).
- The phrase "stops at the first failure" described the runner's behavior as shipped then. The current `reality_gate.sh` runs all gates, aggregates outcomes, and exits non-zero on any failure; the canonical realized graph is documented in `README.md`.
- The gate set listed above was the graph on 2026-11-14. Sovereign writer verification and cockpit structural/coverage verification were added later as top-level gates; see `README.md` for the current graph.
- This entry does not mention the sovereign-writer and cockpit gates because they did not exist at that time. `AGENTS.md §6.4` still describes the older graph and earlier semantics; aligning it is an open item for its owner.

### Changed
- Voice contract enriched earlier today: explicit "we/our" tempered wording in dispatch turns; outside-entity shapes remain refused.

## [2.0.13] — 2026-11-15 — Council pipeline scaled past 128: measured, and the false "lock-free" claim retired

**Who:** build seat (DAXX standard), reviewed against the live framework code.
**Why:** an external reviewer asked how MTPO + council deliberation + the AST gate scale past 128 workers. The honest answer required a measurement, not a restatement of the 64-worker numbers.
**Receipt:** `memory/catch_log/mtpo_ast_gate_scaling_receipt.json` (signed, `tests/test_mtpo_ast_gate_scaling.py`, 15/15 pass).

### Measured
- AST gate cost on a 27-line payload: **196 µs/scan, 166 AST nodes** (Python, GIL-bound).
- `gate_in_path` (AST scan inside the per-transaction critical path, as `CouncilOrchestrator.execute_governed_task` does): **4,174 tx/s @ 64 → 4,042 tx/s @ 512 workers**. Flat. The GIL, not the lock or the rank order, is the ceiling.
- `gate_deferred` (state commit first, scan after, compensate on reject): **3,867–4,110 tx/s**. Same plateau — reordering does not buy throughput while the scanner runs in-process.
- AST gate in a process pool: **7,060 tx/s @ 4 processes**, **6,288 tx/s @ 8** — coordination, not scan cost, saturates next. Tail latency rises to 112–144 ms p99 because futures queue.
- Zero lost updates, zero aborts, Church–Rosser confluence verified at every worker count; a rejected payload compensates its slot and leaves byte-identical state.
- Break-even (commit path = 4,123 tx/s): the gate stops being the bottleneck at ~4,100 workers with 1 s turns, ~20,600 with 5 s turns, ~123,700 with 30 s turns.

### Corrected (honesty)
- `xoras/mtpo.py` described itself as "lock-free" and "guarantees sub-2µs p99 under total contention". It used a single global lock and the number came from a one-increment critical section. Docstring now states it is lock-sharded (six per-slot locks), not lock-free, and points at the receipt for any number. Slot mutation is now an atomic `apply_delta` so concurrent read-modify-write cannot lose updates.
- `xoras/merkle_dag.py` had no synchronization: two threads could both pass the replay check and commit the same payload (TOCTOU), and `get_dynamic_merkle_root` could iterate while `nodes` mutated. `commit`, `promote`, and the root getter are now serialized by an `RLock`; framework suite 141/141 passes.

### Limits stated in the receipt
- Deliberation in the benchmark is a 100–300 µs sleep modelling I/O wait, not a model call. Real council turns are 1–30 s, and at 128+ workers the binding constraint is model-server concurrency, not MTPO or the AST gate.
- Single host. Any cross-node scaling claim still needs a second signed witness.

## [2.0.14] — 2026-11-15 — Scanner provenance reviewed: Rust engine is real but unwired; Byzantine labels corrected

**Who:** build seat, by execution on this host.
**Why:** reviewer asked whether the AST scanner is Zig or Rust, and what the UPGP/dojo Byzantine history actually contains.
**Report:** `docs/audits/SCANNER_AND_BYZANTINE_HISTORY_REVIEW_2026-11-15.md`
**Receipt:** `memory/catch_log/arthur_native_parity_receipt.json`

### Established
- `core/ops/src/arthur_ast_rs` (Rust + tree-sitter-python, 455 LOC) builds natively, **26/26 parity** with the Python scanner on the adversarial corpus, **14.36 µs/scan** in-process (69,644 scans/s) vs Python 196 µs — 13.7× faster.
- It is **not wired**: council uses the Python engine; the only harness shells out through Docker with a hardcoded `/workspace`; the committed binary was Linux x86_64 (`exec format error` on this Mac). Subprocess wiring measures **2.33 ms/scan** — 12× slower than Python.
- No Zig AST scanner exists. `sovra_truth_engine_v4.zig` tokenizes text; the Zig "byzantine" files are plurality vote counters.

### Corrected labels
- `max_byzantine_swarm.zig` and `swarm_ramp.zig` are single-pass plurality counts, not PBFT. Header claim "MAXIMUM BYZANTINE FAULT TOLERANT (PBFT) SWARM ENGINE" is false; yesterday's Grok reply called these rows "Byzantine consensus" — corrected in the report.
- `BYZANTINE_BREAKING_POINT_RAMP_AUDIT.md` ramps no liar density: the script feeds a bad hash and counts provenance rejections.
- `XORAS_015_SWARM_CONSENSUS_LAYER4_VERIFICATION.md` claims Z3 `unsat` for Trinity 2-of-3; no trinity `.smt2` exists. Real artifact is `trinity_gate.py` (file-hash 2-of-3).
- `EXTREME_BYZANTINE_MAXOUT_TELEMETRY.json` has no consensus pillar.
- `core/ops/scripts/byzantine_corruption_sweep` binary is 0 bytes (phantom); quarantine with receipt.

### Confirmed real
- UPGP `tests/exploits/*.c` (ptrace, proc_mem, unshare, bpf, raw_socket) + `RedTeamExploitGauntlet.ts`.
- `trinity_gate.py` 2-of-3 file-hash quorum; `local_quorum_deliberation.py` 3-seat local LLM deliberation; MTPO/cage/UPGP Z3 proofs discharged by `reality_gate.sh`.
- Dojo is empty except `labs/scratch/dojo_test/run_upgp_crash_test.py`.

## [2.0.15] — 2026-11-15 — Months of Byzantine testing reassessed against artifacts (USB included)

**Who:** build seat, by inspection and execution.
**Why:** the first scanner review covered only the live tree. The USB releases and the July–November commit history show a larger body of work, and a different failure pattern.
**Report:** `docs/audits/MONTHS_OF_TESTS_REASSESSMENT_2026-11-15.md`
**Receipt:** `memory/catch_log/governor_veto_state_defect_receipt.json` (reproducer: `core/ops/scripts/governor_veto_state_defect_repro.py`)

### Established
- USB holds two frozen releases (v1.0.0 Sep 28, v1.1.0 Oct 2) with an `ops/stress/` suite that no longer exists live; its Sept 22/28 receipts are real (`8,335 ops/s`, `2,133 DPS @ 400`, 0 desync). Not runnable today: `workspaces/sovra_nexus` is missing.
- 416 commits; 98 test/gauntlet commits. The hardware-stress line is genuine and re-runnable.
- `5m_byzantine_purple_swarm_gauntlet.py` **fabricates** its result: 10 arithmetic batches, no governor call, hard-coded `AIRTIGHT_5M_...PASSED`.
- `30M PBFT` is an in-RAM array evaluation (`1 - rogue_rate`); the Oct 16 receipt says so honestly, then still calls it PBFT.
- The 95% liar-density ramp varies no density — every stage fails on the same `badhash` provenance check.
- `XORAS_015` Z3 claim has no Trinity `.smt2`; `EXTREME_BYZANTINE_MAXOUT_TELEMETRY.json` has no consensus pillar.

### New defect found and receipted
- Governance contradiction veto is defeated by history: row id `sha256(agent:key:timestamp)` lets an `explicit_supersede` write overwrite the honest baseline at the same timestamp, and `score_supersession` uses `fetchone()` with no ordering. After one accepted supersede, unannounced poison is scored 0.95 and **ACCEPTED** (reproduced 2/2).
- Live `.sovereign/hippocampus/governed_memory.db` holds `canonical_mass=666.666` ACCEPTED (3 rows) and `ramp_key_12=stolen_key_corrupt_payload` ACCEPTED.
- Poincaré gate is not in `evaluate_write_candidate`; the "0.00000% contamination" claim is therefore false as wired.

### Fixed
- `triple_intensity_byzantine_poison_gauntlet.py` no longer prints a hard-coded "Hard Veto triggered" when the governor returned ACCEPTED; it prints the actual status.

## [2.0.16] — 2026-11-15 — Poincaré gate wired into the governed-memory write path; UPGP harness made fail-closed

**Who:** build seat, by execution on this host.
**Why:** §2.0.15 established the defect — the governor scored and accepted signed semantic poison because nothing measured semantic distance and an `explicit_supersede` could overwrite the honest baseline. A second defect was found in the same turn: UPGP's own suites printed failures and exited `0`.
**Reports:** `docs/audits/UPGP_RUN_2026-11-15.md`, `docs/audits/MONTHS_OF_TESTS_REASSESSMENT_2026-11-15.md`
**Receipts:** `memory/catch_log/governor_veto_state_defect_receipt.json`, `memory/catch_log/triple_intensity_poison_gate_receipt.json`, `memory/catch_log/governed_memory_quarantine_receipt.json`, `memory/catch_log/QUARANTINE_LEDGER.json` (entry 5), `labs/workspaces/upgp-proving-ground/docs/audits/UPGP_GOVERNED_MEMORY_GATE_RECEIPT.json`, `docs/audits/UPGP_RUN_RECEIPT_2026-11-15.json`

### Added
- `core/ops/memory/poincare_semantic_gate.py` — dependency-free Poincaré metric and a fail-closed `evaluate_transition()`. Scalar values embed as a log-radial point, so two same-sign values satisfy `d_H == |ln(a/b)|` exactly and an in-place write admits at most `e^0.5 ≈ 1.65×` change. Text values are cosmetically normalised first; identical normal forms are admitted, anything else needs a new key version. A sign-class change is maximum drift. The module never raises: any error becomes a veto.
- `tests/test_governor_poincare_gate.py` — 22 acceptance and property tests, including numeric parity with the existing canonical `PoincareManifold` in `labs/workspaces/sovra_nexus/sovra_core/poincare_hypergraph.py`.
- `core/ops/scripts/quarantine_governed_memory_poison.py` — backup, copy, mark, ledger, receipt. Idempotent; deletes nothing.
- `labs/workspaces/upgp-proving-ground/tests/test_governed_memory_gate.py` — UPGP harness that imports the canonical governor instead of reimplementing it; writes its own receipt.

### Fixed
- **The gate is now in the write path, not beside it.** `evaluate_write_candidate()` calls it before scoring and vetoes on any failure. `explicit_supersede` is never a bypass: supersession additionally requires an anchored baseline and a seat in `SUPERSEDE_AUTHORITY = {"jarvis", "maxx"}`.
- **Row identity and read order.** Row ids are unique UUIDs (the old `sha256(agent:key:timestamp)` collided), writes are plain `INSERT` (no silent upsert), and `latest_accepted` orders by `created_at DESC, rowid DESC`. Same-timestamp overwrites are no longer possible.
- **Axis contradiction.** `score_supersession` treated any changed value as a contradiction (S=0.35), which would have vetoed bounded refinements the gate admits. A gate-passing change now scores 0.85; the gate defines the bound and the axis follows it.
- `score_freshness` vetoes timestamps more than 300 s in the future.
- `triple_intensity_byzantine_poison_gauntlet.py` no longer colours a veto as success or an acceptance as failure; it prints the real status and asserts 4/4 vetos. Part 1 is labelled a plurality vote model, not PBFT.
- **UPGP `tests/UPGPProvingGround.test.ts`** set no exit code after printing `[Axis 2] … FAIL`. It now tracks every axis and measured vector, prints `Measured | Not measured | Failures`, and sets `process.exitCode = 1` on failure.
- **UPGP `ops/scripts/run_upgp_full_test_gauntlet.py`** computed failure, printed it, and exited `0`, while dispatching four pre-written speech lines claiming "100 percent perfection". It now builds speech from the measured result, writes `MEASURED VALUES: …` to the run log, requires a clean red-team report, and returns `0`/`1`. Verified with a `node` shim: forced TS failure → `EXIT=1`.

### Quarantined (preserved, not deleted)
- 11 `ACCEPTED` poison rows in `.sovereign/hippocampus/governed_memory.db` — 7 × `ramp_key_12 = stolen_key_corrupt_payload`, 4 × `canonical_mass = 666.666`. Copied intact into `memory_records_quarantine`, originals marked `QUARANTINED`, byte-identical backup at `memory/catch_log/backups/governed_memory_20261115T081220Z.db` (sha256 `8b062157…`, pre-state). Status counts after: 40 ACCEPTED, 11 QUARANTINED, 0 accepted poison. Re-run moves 0.

### Established by execution
- Governor regression: all poison vetoed (d_H = 3.3196 for `18432.0 → 666.666`), 0 poison rows stored, authoritative value `18432.0`, exit 0.
- 22/22 gate tests pass; 4/4 poison attempts vetoed in the hermetic gauntlet; UPGP gate harness PASS.
- UPGP replays: two-layer invariant VETO at d_H = 3.1324 with `SIGBUS` on the physical store and `0.000000%` corruption; Poincaré poison replay VETO at d_H = 3.132398.
- UPGP vector audit: only 3 of 15 named containment vectors measure anything (`VECTOR-01`, `VECTOR-04`, `VECTOR-10`); the other 12 are constants and are now `NOT_MEASURED`. `VECTOR-01` duplicates Axis 1.

### Not established
- Axis 2 (F-test variance ratio) is not a usable measurement on this host: observed 201.8190, 17.2284, 23.9196, 5.9158 and 1.3966 against a `< 1.50` threshold in consecutive runs. A green run must not be quoted.
- No 14-Gate Blackbox Gauntlet was run, so UPGP's own `AGENTS.md` standard for architectural proof is not met by this entry.
- No independent challenger or third-party witness.
- `canonical_mass` and `ramp_key_12` now have **no** `ACCEPTED` row. Re-anchoring them requires a governed, receipted write of a verified value; that is deliberately left open rather than back-filled by hand.
