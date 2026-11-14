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
- **DART DB substrate (Cursor-authored, collective-verified)** — durable DART store: `core/memory/dart_db.py` (hot HexCell ring + append-only WAL + epoch Merkle spine + SQLite cold spill + named rollback checkpoints) and `core/memory/dart_runtime.py` (process-wide singleton, Stage 1 Wake hydration). Reviewed for honesty: dev-machine absolute paths replaced with `__file__`-relative; acceptance suite no longer mutates the live `memory/tri_brain/dart_db` store by default (`DART_LIVE_BOOTSTRAP=1` to opt in); runtime DB dir gitignored; both acceptance suites pass (fresh receipts in `memory/catch_log/DART_*`).
- **DART receipts** — `DART_DB_ACCEPTANCE_RECEIPT.json`, `DART_DB_CHECKPOINT_RECEIPT.json`, `DART_RETROSPECTIVE_RECALL_RECEIPT.json`.
- **Foreign tooling quarantine receipts** — `foreign_tooling_2026-11-14.json` (tracked symlink into vendor config, `.geminiignore`, third-party-branded asset, third-party ADK template).
- **Coverage receipt** — `tts_audio_purge_receipt.json` (54 regenerable TTS artifacts, sha256 each, +0 synthesis cost).

### Removed (per owner directive, TTS cache only)
- 54 regenerable TTS audio files (~39 MB): `memory/agent_logs/collective_chunks/*`, agent briefings, voice drafts, per-turn council recordings, scratch duplicates. Transcripts remain in `turn_ledger.jsonl` and `collective_voice_receipts.jsonl`. Kept: `video_output/combined_audio.m4a`, `docs/assets/thumbnails/video_audio.mp3`, scratch app thumbnail audio. No git-tracked media was lost.

### Changed
- `.gitignore`: `AI_Core/` excluded (Cursor's embedded repository clone, ~3.3 GB — untracked, NOT certified, must not enter the tree or history). `memory/tri_brain/dart_db/` excluded (live runtime store).
- `tests/test_dart_retrospective_recall.py`: explicit `os` import (was relying on `z3` leaking the name).

### Provenance log for untracked items present at 2026-11-14 (not certified; do not treat as production)
- Root-level market/analysis documents (`COMPLETE_MARKET_ECOSYSTEM_SUMMARY.md`, `EXECUTIVE_SUMMARY_AND_FINDINGS.md`, `GOOGLE_SEARCH_VISIBILITY_ANALYSIS.md`, `IMPLEMENTATION_COMPLETE_TODAY.md`, `MARKET_VALUATION_AND_COMPETITIVE_ANALYSIS.md`) — generated mid-session outside the certified surface; recorded here so they are not mistaken for authority. Await owner disposition.
- `.agents/`, `AI_Core/` — agent tooling state and an embedded repository clone; not repository content, not certified, to be excluded or resolved by the owner.
- `.cargo/`, `.upgp-seal`, `.integrity_ledger.json`, `.agents/` — untracked tooling/runtime artifacts; not certified.

### Notes
- Disk reached 100% (130 MB free at the low point) driven primarily by `AI_Core/` (~3.3 GB embedded clone) plus pre-existing `workspaces/` (~2.2 GB), `labs/` (~2.7 GB), `scratch/` (~1.3 GB). No owner data was deleted; the TTS purge reclaimed ~39 MB. Free space must still be addressed by the owner (move `misc/` ~37 GB or `AI_Core/` to external media).

## [2.0.2] — 2026-11-14 — Opportunity map filed

### Added
- `docs/research/AGENTIC_OPPORTUNITY_MAP_2026-11-14.md` — outside-the-box strategy: Proof-of-Action insurance, Agent Black Box (EU AI Act Art. 12), Verify-Before-You-Buy interactive red-team, Stripe-webhook Notary minting, Perpetual Verification Pass, Multi-Witness Federation, public Transparency Log, drift warranty (A_COMBINED/ContextEcho), Proof-Carrying OSS releases, incident forensics retainer, receipt escrow, hardware dead-man's countersign. Non-negotiable caveats documented: no customer validation, three pillar papers not re-measured on our hardware.

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
- `docs/papers/COGNGEN_SSOT_MARKETING_AUDIT.md` — claim-by-claim audit of the user-pasted "COGNEN / SSOT" synthesis: Atlan figures = vendor-published (atlan.com), Fin figures = vendor-published (fin.ai, 12k+ customers, $3.6B Salesforce acquisition pending), CogNGen section misstates arXiv:2310.15177 (drops Σ-precision factor and z̄; ∂F/∂z garbled; sleep-replay update is not the published rule), the code block was executed verbatim on this host and is a random-weight NumPy demo with zero DART/MARS/world_file.db integration ("verified bare-metal" is false), XORAS::OS section invents TCP 8787 and misstates the MARS gate. Verdict: do not cite, do not show externally, fix before any reuse.
- `memory/catch_log/cogngen_ssot_marketing_audit_receipt.json` — verification of record.

## [2.0.7] — 2026-11-14 — OpenCode/CogNGen bridge document audited and marked COMPROMISED

### Added
- `docs/papers/OPENCODE_COGNGEN_BRIDGE_AUDIT.md` — line-level audit of the user-pasted "OpenCode + CogNGen Reality SSOT" synthesis: the cited kernel computes a random-tensor "VFE" (vfe=344.87 measured 2026-11-14) with zero DART/MARS/world_file.db integration; `verify_integrity_v2.py` and `trace.json` do not exist; MARS is misstated as cargo fmt/coverage (actual: AST/SAST/ASAN-TSAN/Z3); ANE/SIMD HexCell mapping is fabricated; AGENTS.md §6.4 Reality Gate added listing the real mandatory gates (6/6 verify_all_production_gates.sh · 7/7 cage lattice · 4/4 side-channel · golden harness). Not for citation or external display.
- `memory/catch_log/opencode_cogngen_bridge_receipt.json` — verification of record.

### Also measured
- Golden question set (v2.0.0-SOVEREIGN, 25 items) answered by local qwen2.5:7b-instruct: mean groundedness 45.2% (n=3 sample), 0 forbidden-hallucination hits, 0 passes at ≥70 threshold — the local 7B model is not grounded on critical security gates; use as a floor signal, not a ceiling claim.
