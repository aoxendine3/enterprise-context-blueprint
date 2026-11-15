# Changelog

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
