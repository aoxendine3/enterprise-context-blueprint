# Legacy Redirects (Phase Draft)

This file tracks temporary redirects that preserve existing workflows while legacy roots are migrated.

## Policy

1. Redirects are temporary and must include owner and sunset date.
2. Redirects are created only after successful migration and verification.
3. Avoid redirect chains; each legacy source should map directly to canonical destination.
4. Remove redirects when call-sites are updated and stable.

## Redirect Registry

| Legacy Path | Redirect Type | Canonical Target | Owner | Created | Sunset | Status | Notes |
|---|---|---|---|---|---|---|---|
| `/Users/ajoxendine68/Desktop/New_Builds` | symlink (optional) | `/Users/ajoxendine68/Desktop/Xoras_Workspace/workspaces/incubation/new-builds` | TBD | 2026-07-04 | TBD | deferred | Phase 2 move completed; redirect intentionally not created in safe tranche |
| `/Users/ajoxendine68/Desktop/Markets` | symlink (planned) | `/Users/ajoxendine68/Desktop/Xoras_Workspace/products/markets` | TBD | TBD | TBD | planned | Reconfirm if destination becomes data-oriented |
| `/Users/ajoxendine68/Desktop/Xoras` | symlink (planned) | `/Users/ajoxendine68/Desktop/Xoras_Workspace/agents` | TBD | TBD | TBD | planned | Requires split with `memory/` target before redirect |
| `/Users/ajoxendine68/Desktop/Xoras_Project` | symlink (planned) | `/Users/ajoxendine68/Desktop/Xoras_Workspace/products/xoras-core` | TBD | TBD | TBD | planned | Final target determined in Phase 4 |
| `/Users/ajoxendine68/Desktop/Xoras_Sovereign_AI_Stack` | symlink (planned) | `/Users/ajoxendine68/Desktop/Xoras_Workspace/ops/sovereign_stack` | TBD | TBD | TBD | planned | Verify launcher paths before cutover |
| `/Users/ajoxendine68/Desktop/sovereign` | shell alias or symlink (planned) | `/Users/ajoxendine68/Desktop/Xoras_Workspace/ops/launchers/sovereign` | TBD | TBD | TBD | planned | Choose alias if scripts embed absolute paths |

## Phase 3 Addendum (No Redirect Creation)

Phase 3 performed split moves only and intentionally created no new redirects. Legacy roots remain in place for path stability until runtime validation and boundary decisions are complete.

| Legacy Path | Redirect Type | Canonical Target | Owner | Created | Sunset | Status | Notes |
|---|---|---|---|---|---|---|---|
| `/Users/ajoxendine68/Desktop/Xoras/AI_Core/Xoras_Agent_Skills` | symlink (optional) | `/Users/ajoxendine68/Desktop/Xoras_Workspace/agents/xoras-agent-skills` | TBD | 2026-07-04 | TBD | deferred | Move completed in Phase 3; redirect intentionally withheld pending dependency check |
| `/Users/ajoxendine68/Desktop/Xoras_Sovereign_AI_Stack/source_code/build_hft.sh` | symlink or launcher update (optional) | `/Users/ajoxendine68/Desktop/Xoras_Workspace/ops/sovereign_stack/scripts/build_hft.sh` | TBD | 2026-07-04 | TBD | deferred | Script moved to `ops`; keep legacy root as compatibility boundary for now |
| `/Users/ajoxendine68/Desktop/Xoras_Sovereign_AI_Stack/source_code/build_hft_shm.sh` | symlink or launcher update (optional) | `/Users/ajoxendine68/Desktop/Xoras_Workspace/ops/sovereign_stack/scripts/build_hft_shm.sh` | TBD | 2026-07-04 | TBD | deferred | Script moved to `ops`; avoid redirect until call sites are audited |
| `/Users/ajoxendine68/Desktop/Xoras_Sovereign_AI_Stack/deployment_package/com.xoras.archivist.plist` | symlink (optional) | `/Users/ajoxendine68/Desktop/Xoras_Workspace/ops/config/sovereign_stack/com.xoras.archivist.plist` | TBD | 2026-07-04 | TBD | deferred | Config file relocated; no symlink created in safe tranche |
| `/Users/ajoxendine68/Desktop/Xoras_Sovereign_AI_Stack/builds/libxoras_alloc.dylib` | symlink (optional) | `/Users/ajoxendine68/Desktop/Xoras_Workspace/dist/sovereign_stack/libxoras_alloc.dylib` | TBD | 2026-07-04 | TBD | deferred | Non-runtime artifact moved to `dist`; verify loader references before redirect |

## Redirect Command Templates (Do Not Run Yet)

```bash
ln -s "/Users/ajoxendine68/Desktop/Xoras_Workspace/workspaces/incubation" "/Users/ajoxendine68/Desktop/New_Builds"
ln -s "/Users/ajoxendine68/Desktop/Xoras_Workspace/products/markets" "/Users/ajoxendine68/Desktop/Markets"
```

Use only after the corresponding source data has been migrated and validated.

## Phase 4 Low-Risk Addendum (No Redirect Creation)

Phase 4 low-risk consolidation moved docs/assets/dist artifacts only and intentionally created no redirects in this tranche.

| Legacy Path | Redirect Type | Canonical Target | Owner | Created | Sunset | Status | Notes |
|---|---|---|---|---|---|---|---|
| `/Users/ajoxendine68/Desktop/Xoras.app` | symlink (optional) | `/Users/ajoxendine68/Desktop/Xoras_Workspace/dist/Xoras.app` | TBD | 2026-07-04 | TBD | deferred | Artifact moved successfully; redirect intentionally withheld pending launcher/path audit |
| `/Users/ajoxendine68/Desktop/Xoras_Sovereign_AI_Stack.dmg` | symlink (optional) | `/Users/ajoxendine68/Desktop/Xoras_Workspace/dist/Xoras_Sovereign_AI_Stack.dmg` | TBD | 2026-07-04 | TBD | deferred | Artifact moved successfully; no symlink needed for standard distribution flow |
| `/Users/ajoxendine68/Desktop/Xoras_Workspace/Documents_and_Analysis/Docs` | symlink (optional) | `/Users/ajoxendine68/Desktop/Xoras_Workspace/docs/legacy-documents-and-analysis/Docs` | TBD | 2026-07-04 | TBD | deferred | Legacy docs moved; left without redirect to avoid masking stale references |
| `/Users/ajoxendine68/Desktop/Xoras_Workspace/Documents_and_Analysis/Documentation` | symlink (optional) | `/Users/ajoxendine68/Desktop/Xoras_Workspace/docs/legacy-documents-and-analysis/Documentation` | TBD | 2026-07-04 | TBD | deferred | Legacy documentation moved; redirect deferred until call-site audit |
| `/Users/ajoxendine68/Desktop/Xoras_Workspace/Documents_and_Analysis/My prompts` | symlink (optional) | `/Users/ajoxendine68/Desktop/Xoras_Workspace/docs/prompts/My prompts` | TBD | 2026-07-04 | TBD | deferred | Prompt directory normalized into canonical docs tree |

## Phase 5 High-Risk Addendum (Dry-Run Only)

No redirects were created in the high-risk dry-run stream. Path-sensitive redirects remain gated behind per-batch verification and rollback checkpoints.

| Legacy Path | Redirect Type | Canonical Target | Owner | Created | Sunset | Status | Notes |
|---|---|---|---|---|---|---|---|
| `/Users/ajoxendine68/Desktop/Xoras_Workspace/Dev_Workspaces/GitHub_Repos` | directory symlink (planned) | `/Users/ajoxendine68/Desktop/Xoras_Workspace/workspaces/active/github-repos` | TBD | TBD | TBD | blocked | Only after per-repo git health checkpoints pass for each batch |
| `/Users/ajoxendine68/Desktop/Xoras_Workspace/AI_Core/Xoras_Project` | directory symlink (planned) | `/Users/ajoxendine68/Desktop/Xoras_Workspace/products/xoras-core` | TBD | TBD | TBD | blocked | Nested repo/runtime ownership unresolved; redirect deferred until move batch completes |
| `/Users/ajoxendine68/Desktop/Xoras` | directory symlink (planned) | `/Users/ajoxendine68/Desktop/Xoras_Workspace/agents` + `/Users/ajoxendine68/Desktop/Xoras_Workspace/memory` | TBD | TBD | TBD | blocked | Legacy root currently a lightweight stub; avoid masking stale call-sites |
| `/Users/ajoxendine68/Desktop/Xoras_Project` | directory symlink (planned) | `/Users/ajoxendine68/Desktop/Xoras_Workspace/products/xoras-core` or `workspaces/active/xoras-core` | TBD | TBD | TBD | blocked | Final canonical ownership must be locked first |
| `/Users/ajoxendine68/Desktop/sovereign` | wrapper replacement/symlink (planned) | `/Users/ajoxendine68/Desktop/Xoras_Workspace/ops/launchers/sovereign` | TBD | TBD | TBD | blocked | Current wrapper executes absolute home path; redirect requires dual-run smoke test and rollback script |

High-risk redirect creation criteria:

1. Source and target trees both snapshot-clean for current batch (inventory + size delta recorded).
2. Repo probes complete for batch targets (`rev-parse`, branch/head capture, remote presence).
3. Runtime launch smoke checks pass for affected entrypoints.
4. Rollback command block is prepared and tested in dry-run mode before redirect creation.
