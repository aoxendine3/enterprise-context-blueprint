# Migration Manifest (Draft)

This manifest defines intended source-to-destination mappings for the Xoras Agent-OS reorganization.

- Status values:
  - `planned` - mapped but not executed
  - `in-progress` - currently being migrated
  - `migrated` - move completed and verified
  - `blocked` - cannot proceed without prerequisite
- Risk levels:
  - `low` - non-runtime artifacts; easy rollback
  - `medium` - mixed content, some path sensitivity
  - `high` - repo/runtime/path-sensitive

## Build Phase 1 Scope

Phase 1 is non-destructive. It establishes inventory and target layout. Moves are limited to clearly low-risk artifacts only; all others remain planned.

## Mapping Table

| Source | Destination | Phase | Risk | Status | Notes |
|---|---|---|---|---|---|
| `/Users/ajoxendine68/Desktop/New_Builds` | `workspaces/incubation/new-builds` | 2 | medium | migrated | Completed with guarded precondition checks and normalized destination naming |
| `/Users/ajoxendine68/Desktop/Markets` | `products/markets/` | 2 | medium | planned | If dataset-heavy, evaluate split to `memory/markets` or `assets/markets` |
| `/Users/ajoxendine68/Desktop/Xoras` | `agents/` + `memory/` | 5-highrisk | high | in-progress | Remaining root is a small legacy stub (`AI_Core` empty); defer final archival/redirect until batch-4 cutover |
| `/Users/ajoxendine68/Desktop/Xoras_Project` | `products/xoras-core/` or `workspaces/active/xoras-core/` | 5-highrisk | high | in-progress | Dry-run shows residual `xoras-core` tree; final destination coupled to repo ownership and runtime entrypoints |
| `/Users/ajoxendine68/Desktop/Xoras_Sovereign_AI_Stack` | `ops/sovereign_stack/` + `memory/` | 3 | high | in-progress | Safe split completed for ops scripts/config + dist artifact; runtime source/docs/tests remain blocked pending boundary decision |
| `/Users/ajoxendine68/Desktop/Xoras.app` | `dist/` | 4-lowrisk | low | migrated | Moved to canonical `dist/` in low-risk consolidation tranche |
| `/Users/ajoxendine68/Desktop/Xoras_Sovereign_AI_Stack.dmg` | `dist/` | 4-lowrisk | low | migrated | Moved to canonical `dist/` in low-risk consolidation tranche |
| `/Users/ajoxendine68/Desktop/Xoras_Workspace/Documents_and_Analysis` | `docs/` | 4-lowrisk | low | migrated | Normalized into `docs/analysis`, `docs/prompts`, and `docs/legacy-documents-and-analysis` |
| `/Users/ajoxendine68/Desktop/Xoras_Workspace/Backups_and_Configs` | `archives/` + `ops/config/` | 1 | medium | planned | Split backup payloads from live config files |
| `/Users/ajoxendine68/Desktop/Xoras_Workspace/Dev_Workspaces/GitHub_Repos` | `workspaces/active/` | 5-highrisk | high | in-progress | Dry-run complete with topology/runtime sampling; execution blocked pending per-repo git clean/remote checkpointing |
| `/Users/ajoxendine68/Desktop/Xoras_Workspace/AI_Core/Xoras_Project` | `products/xoras-core/` | 5-highrisk | high | in-progress | Dry-run complete; nested-repo and runtime boundaries identified, move execution gated by repo health checks |
| `/Users/ajoxendine68/Desktop/sovereign` | `ops/launchers/sovereign` | 5-highrisk | high | in-progress | Wrapper is path-sensitive (`exec` to absolute home path); requires staged redirect with rollback |

## Phase 1 Executed Changes

- Created canonical folders only (non-destructive):
  - `workspaces/active`
  - `workspaces/incubation`
  - `workspaces/experimental`
  - `agents`
  - `memory`
  - `ops/config`
  - `ops/reports/reorg`
  - `products`
  - `assets`
  - `docs`
  - `archives/legacy_roots`
  - `dist`
  - `scratch`

## Phase 2 Executed Changes

- Migrated:
  - `/Users/ajoxendine68/Desktop/New_Builds` -> `workspaces/incubation/new-builds`
- Safety controls used:
  - source existence check
  - destination collision check
  - no-force move (abort on any blocker)
- Verification artifacts:
  - `ops/reports/reorg/inventory-before-phase2.md`
  - `ops/reports/reorg/inventory-after-phase2.md`
  - `ops/reports/reorg/size-delta-phase2.csv`
  - `ops/reports/reorg/verification-phase2.md`

## Phase 3 Executed Changes

- Migrated (classification + split only; no repo-root relocation):
  - `/Users/ajoxendine68/Desktop/Xoras/AI_Core/Xoras_Agent_Skills` -> `agents/xoras-agent-skills`
  - `/Users/ajoxendine68/Desktop/Xoras_Sovereign_AI_Stack/deployment_package/com.xoras.archivist.plist` -> `ops/config/sovereign_stack/com.xoras.archivist.plist`
  - `/Users/ajoxendine68/Desktop/Xoras_Sovereign_AI_Stack/source_code/build_hft.sh` -> `ops/sovereign_stack/scripts/build_hft.sh`
  - `/Users/ajoxendine68/Desktop/Xoras_Sovereign_AI_Stack/source_code/build_hft_shm.sh` -> `ops/sovereign_stack/scripts/build_hft_shm.sh`
  - `/Users/ajoxendine68/Desktop/Xoras_Sovereign_AI_Stack/builds/libxoras_alloc.dylib` -> `dist/sovereign_stack/libxoras_alloc.dylib`
- Blocked/retained in place (risk/ambiguity gate):
  - `source_code/*.cpp`, `source_code/*.h`, `source_code/xoras_memory_core.py`
  - `documentation/`, `test_results/`, and stack `README.md`
- Verification artifacts:
  - `ops/reports/reorg/inventory-before-phase3.md`
  - `ops/reports/reorg/inventory-after-phase3.md`
  - `ops/reports/reorg/size-delta-phase3.csv`
  - `ops/reports/reorg/verification-phase3.md`

## Phase 4 Low-Risk Executed Changes

- Migrated (strict low-risk only):
  - `/Users/ajoxendine68/Desktop/Xoras_Workspace/Documents_and_Analysis/Docs` -> `docs/legacy-documents-and-analysis/Docs`
  - `/Users/ajoxendine68/Desktop/Xoras_Workspace/Documents_and_Analysis/Documentation` -> `docs/legacy-documents-and-analysis/Documentation`
  - `/Users/ajoxendine68/Desktop/Xoras_Workspace/Documents_and_Analysis/My prompts` -> `docs/prompts/My prompts`
  - `/Users/ajoxendine68/Desktop/Xoras_Workspace/Documents_and_Analysis/ONYX_Comparison_Report.md` -> `docs/analysis/ONYX_Comparison_Report.md`
  - `/Users/ajoxendine68/Desktop/Xoras_Workspace/Documents_and_Analysis/corporate_finance_fully_robust_model.xlsx` -> `docs/analysis/corporate_finance_fully_robust_model.xlsx`
  - `/Users/ajoxendine68/Desktop/Xoras_Workspace/Documents_and_Analysis/corporate_finance_innovative_model.xlsx` -> `docs/analysis/corporate_finance_innovative_model.xlsx`
  - `/Users/ajoxendine68/Desktop/Xoras_Workspace/Documents_and_Analysis/corporate_finance_monte_carlo.xlsx` -> `docs/analysis/corporate_finance_monte_carlo.xlsx`
  - `/Users/ajoxendine68/Desktop/Xoras_Workspace/Documents_and_Analysis/Documentation/Finance/receipt.jpg` -> `assets/media/finance/receipt.jpg`
  - `/Users/ajoxendine68/Desktop/Xoras_Workspace/Documents_and_Analysis/Documentation/Forms/Vendor Registration Form.pdf` -> `assets/collateral/forms/Vendor Registration Form.pdf`
  - `/Users/ajoxendine68/Desktop/Xoras.app` -> `dist/Xoras.app`
  - `/Users/ajoxendine68/Desktop/Xoras_Sovereign_AI_Stack.dmg` -> `dist/Xoras_Sovereign_AI_Stack.dmg`
- Blocked/retained in place:
  - `/Users/ajoxendine68/Desktop/Markets` (classification ambiguous)
  - `/Users/ajoxendine68/Desktop/Xoras` (runtime/repo boundary unresolved)
  - `/Users/ajoxendine68/Desktop/Xoras_Project` (repo-root/high-risk)
  - `/Users/ajoxendine68/Desktop/Xoras_Sovereign_AI_Stack` root remainder (runtime source/test/docs mix)
  - Empty shell `/Users/ajoxendine68/Desktop/Xoras_Workspace/Documents_and_Analysis` retained (no destructive delete)
- Verification artifacts:
  - `ops/reports/reorg/inventory-before-phase4-lowrisk.md`
  - `ops/reports/reorg/inventory-after-phase4-lowrisk.md`
  - `ops/reports/reorg/size-delta-phase4-lowrisk.csv`
  - `ops/reports/reorg/verification-phase4-lowrisk.md`

## Phase 5 High-Risk Dry-Run Stream (No Moves Yet)

- Scope enforced to high-risk units only:
  - `/Users/ajoxendine68/Desktop/Xoras_Workspace/Dev_Workspaces/GitHub_Repos`
  - `/Users/ajoxendine68/Desktop/Xoras_Workspace/AI_Core/Xoras_Project`
  - `/Users/ajoxendine68/Desktop/Xoras`
  - `/Users/ajoxendine68/Desktop/Xoras_Project`
  - `/Users/ajoxendine68/Desktop/sovereign`
- Safe prep actions executed:
  - generated bounded topology/dependency probes only
  - created high-risk verification docs and sample health artifacts
  - performed no moves, deletes, symlink creation, or destructive git operations
- Probe highlights:
  - `Dev_Workspaces/GitHub_Repos` size observed at `12879548 KB` with `14` top-level entries and `80` runtime markers sampled to depth-2
  - `AI_Core/Xoras_Project` size observed at `5274172 KB` with root `.git` + multiple nested repo-like directories and `6` runtime markers sampled
  - `Desktop/Xoras` and `Desktop/Xoras_Project` appear as small residual roots (`8 KB` and `3328 KB`)
  - `Desktop/sovereign` is a launcher wrapper with absolute path execution (`/Users/ajoxendine68/sovereign/.venv/bin/sovereign`)
- Blockers captured:
  - full-tree repo discovery/path scans timed out on large roots during bounded scans; execution phase must run per-batch sampled checkpoints (not one-shot full recursion)
- Verification artifacts:
  - `ops/reports/reorg/highrisk-topology-probe.json`
  - `ops/reports/reorg/highrisk-dryrun-inventory.json`
  - `ops/reports/reorg/highrisk-size-and-repo-summary.csv`
  - `ops/reports/reorg/highrisk-repo-health-sampled.json`
  - `ops/reports/reorg/verification-phase5-highrisk.md`

## Verification Artifacts

- Inventory snapshots and size deltas are written to: `ops/reports/reorg/`
- Use these files as authoritative before/after checkpoints for subsequent phases.
