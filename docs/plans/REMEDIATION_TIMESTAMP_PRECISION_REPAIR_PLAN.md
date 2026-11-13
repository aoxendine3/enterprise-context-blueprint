# Remediation Plan: Timestamp Precision Mutation + Writer-Provenance References

**Status:** PLANNED → EXECUTING (gated)
**Date:** 2026-11-13
**Mandate source:** User directive — failsafe rollback stages, step-back-and-brainstorm
on timestamp conflicts, gated proofs, full consensus with unbiased tie-breaker.
**Rollback snapshot:** `memory/rollback/snapshots/20261113T035606_pre_timestamp_repair_and_writer_ref`

## 1. Findings (evidence-backed)

| # | Finding | Proof |
|---|---------|-------|
| F1 | 3 nodes (seq 10,11,12, session `anti_corruption_test_session` in `.sovereign/provenance/lineage_dag.db`) fail `NODE_METADATA_TAMPERING_DETECTED` | verifier output 2026-11-13 |
| F2 | Their HMAC signatures verify against the recorded node_ids → node_ids are authentic | HMAC re-check via `ContextLineageEngine.compute_hmac` |
| F3 | The `timestamp` column values were mutated post-commit (precision lost: 6→4/5 decimals) | brute-force recovery: `1794523906.673698`, `1794523979.322391`, `1794523979.355271` all reproduce the recorded node_ids exactly |
| F4 | Nodes do not exist in the pre-reconcile backup → appended after reconciliation; reconcile process not the culprit | backup DB query, 0 rows seq 9–13 |
| F5 | No other DB in the repo contains these node_ids | full repo DB scan |
| F6 | Root cause of the mutation NOT yet identified | open item — catch_log audit pending |
| F7 | Canonical store (3,262 nodes) and mirror (3,286) diverged by 24 nodes appended by Our own audit engine runs | db_inventory_audit crosscheck |

## 2. Options considered (brainstorm)

- **O1 — Rewrite node_ids to match current (mutated) timestamps.** REJECTED: destroys authentic commit history; rewards the mutation.
- **O2 — Quarantine the 3 nodes.** REJECTED as sole action: breaks parent chain for seq 13+; loses authentic evidence.
- **O3 — Restore the true original timestamps (provable by hash), add writer-provenance references so every timestamp is anchored to a writer-log entry + merkle chain going forward.** CHOSEN.

## 3. Execution stages (each gated)

1. **Rollback stage (DONE):** snapshot of both DBs + engine script; manifest hashed.
2. **Schema stage:** add `writer_log_ref` column (TEXT, nullable) to `lineage_nodes` in canonical + mirror DBs; backfill legacy rows with `LEGACY_PRE_WRITER_REF`.
3. **Writer-log stage:** every future commit appends a line to `memory/catch_log/writer_log.jsonl` (ts, node_id, writer, step_type, merkle root, script, pid); the node stores the SHA-256 of that line in `writer_log_ref`. Bidirectional, fail-closed linkage.
4. **Repair stage:** UPDATE the 3 timestamps to the hash-proven originals; set `writer_log_ref` on repaired rows to the repair receipt hash.
5. **Proof stage:** (a) verifier → 0 violations; (b) HMAC re-verify all 3; (c) dual-witness gate pass (requires journal-mode fix, separate item); (d) re-run reconcile to re-sync canonical↔mirror.
6. **Consensus stage:** Trinity Gate 2-of-3 audio hashes + independent verifier dissent review before declaring final.
7. **Receipt stage:** full receipt in `memory/catch_log/timestamp_repair_receipt.json`.

## 4. Non-goals / invariants
- No deletion of any file. No barn/ access. Immutable-file flags untouched (Log Entry #079).
- Legacy nodes are NOT rewritten beyond the 3 hash-proven timestamp restorations.
