# Phase 5 High-Risk Verification Checks (Dry-Run Stream)

Generated at: `2026-07-04T08:05:00Z`

## Scope (Strictly Enforced)

- `/Users/ajoxendine68/Desktop/Xoras_Workspace/Dev_Workspaces/GitHub_Repos`
- `/Users/ajoxendine68/Desktop/Xoras_Workspace/AI_Core/Xoras_Project`
- `/Users/ajoxendine68/Desktop/Xoras`
- `/Users/ajoxendine68/Desktop/Xoras_Project`
- `/Users/ajoxendine68/Desktop/sovereign`

## Checks Performed

- Existence/type verification for all five high-risk targets.
- Size probes (`du -sk`) captured for each target.
- Topology probe executed for high-risk trees:
  - top-level entry counts
  - top-level repo-candidate directories
  - depth-2 runtime/dependency markers (`package.json`, `pyproject.toml`, `requirements.txt`, `go.mod`).
- Sampled repo-health probes with short timeouts (non-destructive):
  - `git rev-parse --is-inside-work-tree`
  - branch/head capture where available
  - remote-count capture where available
- Path-sensitive launcher validation:
  - `/Users/ajoxendine68/Desktop/sovereign` checked and confirmed as absolute-path wrapper.
- No migration actions executed (dry-run only).

## Probe Results (High-Level)

- `/Users/ajoxendine68/Desktop/Xoras_Workspace/Dev_Workspaces/GitHub_Repos`
  - size: `12879548 KB`
  - top-level entries: `14`
  - runtime markers sampled to depth-2: `80`
  - notable structure includes `Active`, `Research`, `Utilities`, `project`, `xoras-sentry`
- `/Users/ajoxendine68/Desktop/Xoras_Workspace/AI_Core/Xoras_Project`
  - size: `5274172 KB`
  - top-level entries: `10`
  - root `.git` observed, plus nested repo-like directories (`DualStreamHandler`, `xoras-app`, `xoras-config`, `xoras-core`)
  - runtime markers sampled to depth-2: `6`
- `/Users/ajoxendine68/Desktop/Xoras`
  - size: `8 KB`
  - appears as lightweight legacy stub with `AI_Core` shell
- `/Users/ajoxendine68/Desktop/Xoras_Project`
  - size: `3328 KB`
  - residual `xoras-core` subtree remains
- `/Users/ajoxendine68/Desktop/sovereign`
  - shell wrapper (`2` lines) executes absolute path:
    - `exec "/Users/ajoxendine68/sovereign/.venv/bin/sovereign" "$@"`

## Safe Prep Actions Completed

- Created/updated high-risk dry-run artifacts only:
  - `ops/reports/reorg/highrisk-topology-probe.json`
  - `ops/reports/reorg/highrisk-dryrun-inventory.json`
  - `ops/reports/reorg/highrisk-size-and-repo-summary.csv`
  - `ops/reports/reorg/highrisk-repo-health-sampled.json`
  - this report (`verification-phase5-highrisk.md`)
- Updated planning docs:
  - `MIGRATION_MANIFEST.md`
  - `LEGACY_REDIRECTS.md`
- Performed no moves, deletes, renames, symlink creation, or destructive git operations.

## Blocked / Risky Items

- Full recursive repo/path discovery on the two largest trees exceeded bounded dry-run time windows.
  - observed as timed-out probes in `highrisk-dryrun-inventory.json`.
  - implication: execution must use segmented batch checkpoints, not monolithic scans.
- Git health probes with very short timeouts on large repos are inconclusive.
  - implication: run per-batch repo checkpoints with tuned timeout budget before each real move.
- `sovereign` wrapper is path-sensitive to `/Users/ajoxendine68/sovereign/.venv/bin/sovereign`.
  - implication: treat wrapper migration as dedicated final batch with dual-path rollback.

## Per-Batch Migration Protocol (Execution Blueprint)

### Batch 1 - `Desktop/Xoras` legacy stub

Checkpoint criteria (pre-move):
- Confirm `Desktop/Xoras/AI_Core` is still empty.
- Confirm no runtime launcher references still point to `Desktop/Xoras`.
- Snapshot: size + directory listing.

Move action (future execution):
- Rehome remaining stub to `archives/legacy_roots/Xoras` (or remove empty shell only after archive snapshot).

Rollback notes:
- Restore archived stub back to `/Users/ajoxendine68/Desktop/Xoras`.
- Revalidate launcher references.

---

### Batch 2 - `Desktop/Xoras_Project` residual tree

Checkpoint criteria (pre-move):
- Capture repo ownership decision (`products/xoras-core` vs `workspaces/active/xoras-core`).
- Verify repo root(s), remotes, and branch/head metadata for `xoras-core`.
- Snapshot: size + file inventory.

Move action (future execution):
- Move `Desktop/Xoras_Project/xoras-core` to approved canonical destination.

Rollback notes:
- Move canonical `xoras-core` back to `/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core`.
- Re-run repo metadata probe and smoke import/run check.

---

### Batch 3 - `AI_Core/Xoras_Project` (root + nested repos)

Checkpoint criteria (pre-move):
- Partition nested directories by ownership:
  - product runtime
  - config/ops
  - archive/legacy
- For each repo batch segment: capture `rev-parse`, branch, HEAD, remote list, and dirty status.
- Record runtime entrypoint matrix for `xoras-app`, `xoras-core`, `xoras-config`, and `DualStreamHandler`.

Move action (future execution):
- Move in segments (not whole-root move):
  - segment A: config/ops-safe
  - segment B: product runtime repos
  - segment C: residual support trees

Rollback notes:
- Reverse each segment independently using segment-specific source/destination map.
- Do not continue to next segment until previous segment smoke checks pass.

---

### Batch 4 - `Dev_Workspaces/GitHub_Repos` (largest repo-heavy tree)

Checkpoint criteria (pre-move):
- Split into sub-batches by top-level groups: `Active`, `Research`, `Utilities`, `project`, `xoras-sentry`.
- For each sub-batch:
  - collect per-repo git health and remote map
  - capture dependency marker summary
  - verify no destination collisions
- Reserve enough timeout budget for repo status checks; avoid one-shot full-tree probes.

Move action (future execution):
- Move one sub-batch at a time to `workspaces/active/github-repos/<group>`.

Rollback notes:
- Reverse only the current sub-batch if any checkpoint fails.
- Preserve untouched groups in-place until all prior groups verify cleanly.

---

### Batch 5 - `Desktop/sovereign` wrapper cutover (final)

Checkpoint criteria (pre-move):
- Create canonical wrapper at `ops/launchers/sovereign` with path strategy documented.
- Validate both old and new wrapper invocations produce same behavior.
- Decide redirect style (symlink vs wrapper shim) and owner/sunset date.

Move action (future execution):
- Move/replace legacy wrapper with approved redirect approach.

Rollback notes:
- Recreate original wrapper content exactly:
  - `#!/usr/bin/env bash`
  - `exec "/Users/ajoxendine68/sovereign/.venv/bin/sovereign" "$@"`
- Re-run wrapper smoke command.

## Exact Next Execution Order (For Real High-Risk Moves)

1. Lock repo-timeout/checkpoint template and run Batch 1 (`Desktop/Xoras` stub).
2. Execute Batch 2 (`Desktop/Xoras_Project/xoras-core`) with explicit destination decision.
3. Execute Batch 3 (`AI_Core/Xoras_Project`) in segmented repo groups.
4. Execute Batch 4 (`Dev_Workspaces/GitHub_Repos`) by top-level sub-batch (`Active` -> `Research` -> `Utilities` -> `project` -> `xoras-sentry`).
5. Execute Batch 5 (`Desktop/sovereign`) wrapper cutover and redirect registration.
6. After each batch: publish before/after inventory, size delta, repo checkpoint log, runtime smoke checks, and rollback status.
