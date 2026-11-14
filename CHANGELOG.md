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
