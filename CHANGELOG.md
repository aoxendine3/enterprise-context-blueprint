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
