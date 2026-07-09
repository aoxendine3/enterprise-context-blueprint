# Deduplication Manifest

**Generated:** 2026-07-04  
**Method:** Name + path cross-check, targeted hash sampling, migration manifest cross-reference  
**USB:** `/Volumes/USB_Backup` not mounted. `/Volumes/sovereign_stack` mounted but empty of zenith/key files.

## Summary

| Category | Count | Action |
|----------|-------|--------|
| KEEP (canonical) | 12 roots | No move |
| ARCHIVE-TO-USB (when mounted) | 4 groups | Offload after Anthony approves |
| DELETE-CANDIDATE (exact dupes only) | 2 items | Safe after manifest approval |
| LEGACY STUB (redirect, don't delete) | 3 Desktop folders | Archive in Phase 5 |

**Disk recovered earlier today:** 4.45 GiB (cache + broken symlinks per `high-confidence-cleanup-report.md`).  
**Current disk:** 7.4 GiB free (68% used).

---

## KEEP — Canonical Copies

| Item | Canonical Path | Why Keep |
|------|----------------|----------|
| Xoras workspace root | `~/Desktop/Xoras_Workspace/` | Single source of truth per `ROOTS.md` |
| xoras-core runtime | `AI_Core/Xoras_Project/xoras-core/` | Active wake, memory, daemon |
| xoras-app (Tauri) | `AI_Core/Xoras_Project/xoras-app/` | Desktop command center |
| zenith_env.sh | `Backups_and_Configs/_System_Config/sovereign_keys/zenith_env.sh` | Shell env loader (fixed in .zshrc) |
| Xoras.app bundle | `dist/Xoras.app` | Release artifact |
| Sovereign DMG | `dist/Xoras_Sovereign_AI_Stack.dmg` | Release artifact (200 KB) |
| Agent skills | `agents/xoras-agent-skills/` | Migrated from legacy Xoras |
| Ops configs | `ops/config/`, `ops/sovereign_stack/` | Live deployment glue |
| New builds incubation | `workspaces/incubation/new-builds/` | Phase 2 migration complete |

---

## ARCHIVE-TO-USB (When USB_Backup Mounted)

| Group | Paths | Est. Size | Notes |
|-------|-------|-----------|-------|
| Backups_and_Configs bulk | `Backups_and_Configs/_Archive/` | ~1.2 GB | Cold history, github audits, Maxx sandbox |
| Sovereign stack builds | `dist/sovereign_stack/` | Small | `libxoras_alloc.dylib` — backup copy |
| Desktop legacy DMG (if reappears) | Any second `Xoras_Sovereign_AI_Stack.dmg` on Desktop | 200 KB | Hash-compare before delete |
| Dev_Workspaces mirror | `Dev_Workspaces/GitHub_Repos/` duplicates of `workspaces/active/` | TBD | Blocked until per-repo git health check |

**USB target structure:**
```
/Volumes/USB_Backup/Xoras_Cold_Archive/2026-07-04/
  ├── backups_and_configs_archive/
  ├── dist_artifacts/
  └── dedupe_manifest.json
```

---

## DELETE-CANDIDATE — Exact Duplicates Only

> **Not executed in this pass.** Requires Anthony approval.

| File | Copies | Keep | Delete Candidate | Confidence |
|------|--------|------|------------------|------------|
| Broken symlinks (already deleted) | 3 in `_Archive/History/github_audits/` | — | Done ✓ | HIGH |
| `xoras-app/dist/` build output | Mirrors `dist/` partial assets | `dist/` at workspace root | `xoras-app/dist/` if hash-match | MEDIUM — verify vite rebuild first |

---

## LEGACY STUBS — Redirect, Do Not Delete Yet

| Desktop Path | Size | Status | Destination (planned) |
|--------------|------|--------|----------------------|
| `~/Desktop/Xoras` | 8 KB | Empty stub (`AI_Core` empty) | `archives/legacy_roots/xoras/` |
| `~/Desktop/Xoras_Project` | 4.9 MB | Residual tree | `products/xoras-core/` or archive |
| `~/Desktop/Xoras_Sovereign_AI_Stack` | 4 KB | Ops split done; stub remains | `ops/sovereign_stack/` + archive |
| `~/Desktop/Projects` | Small | antigravity path still referenced in .zshrc | Migrate `ANTIGRAVITY_HOME` when ready |

---

| Safe Moves Executed This Pass

| Action | Result |
|--------|--------|
| Broken symlink cleanup | Already done (Phase 4 cleanup) |
| Stale daemon logs archived | **Done** — 4.2 MB moved from `Desktop/Xoras_Project/.../Omni_Dojo_Sandbox/` to `archives/legacy_roots/desktop-xoras-project-stale-logs-20260704/` |
| USB offload | **Ready** — run `bash ops/scripts/archive-to-usb.sh` when USB_Backup is mounted (~683 MB _Archive) |
| Delete xoras-app/dist duplicate | **Skipped** — pending hash verification + npm build completion |

---

## Approval Checklist (Anthony)

- [ ] Mount USB_Backup and confirm free space ≥ 5 GB
- [ ] Review ARCHIVE-TO-USB table above
- [ ] Say "approve dedupe archive" to agent — agent moves, does not delete unique content
- [ ] Say "approve legacy stub archive" for Desktop Xoras/Xoras_Project/Xoras_Sovereign_AI_Stack
