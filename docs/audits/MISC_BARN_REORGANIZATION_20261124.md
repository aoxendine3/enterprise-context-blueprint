# `misc/` → Barn Reorganization — 2026-11-24

**Status:** EXECUTED. Operator directive: move nonessential cache, duplicate, and placeholder material out of the active project tree into the barn. **Nothing was deleted.**
**Destination:** `barn/archives/the_barn/misc_reorganize_20261124/`
**Full manifest:** `barn/archives/the_barn/misc_reorganize_20261124/MANIFEST.json`
**Summary receipt:** `memory/catch_log/MISC_BARN_MOVE_SUMMARY_20261124.json`

## 1. What moved

| Category | Files | Why |
| :--- | ---: | :--- |
| Chrome cache data (`hex16_N`) | 62,259 | Browser cache spill, no build or project caller |
| Cache index names (32-hex / numeric) | 1,090 | Browser index residue |
| Compiled Python (`.pyc`) | 7,110 | Regenerable bytecode |
| Source maps (`.map`) | 5,588 | Regenerable build output |
| Object files (`.o`) | 2,358 | Compiled artifacts, no source in the active tree |
| Build metadata (`.toc`, `.meta`, `.plist`, `.gemspec`, `.mts`) | 2,542 | Regenerable packaging metadata |
| Journals (`.journal`) | 557 | Cache journal residue |
| Stale duplicate images (`Docker.raw`, `disk`) | 2 | Unreferenced virtual disks; live Docker Desktop disk exists separately |
| Historical app database (`xoras.db`) | 1 | Unreferenced by any live process; preserved intact in cold archive |

**Total moved: 81,507 files**, 274.04 GB apparent size. Allocated space moved: about 13 GB (the apparent size is sparse). `misc/` dropped from ~25.7 GiB allocated to ~13 GiB; the barn destination now holds ~13 GiB.

## 2. Proof before and after the move

- **Live-reference sweep:** 59,294 canonical source files scanned. Every `misc/` reference in active source was examined. One live-referenced family was found: `hhv_lattice*.rcgu.o`, cited by `core/ops/provenance/seed_ledger.py` and `core/ops/provenance/physical_artifact_audit.py` as physical evidence.
- **Restore before sign-off:** the 68 matching provenance objects were moved **back** to `misc/` with inode verification. They are recorded under `resolved_not_moved` in `memory/catch_log/QUARANTINE_LEDGER.json`. Referenced evidence is never quarantined.
- **Per-file verification:** every one of the 81,507 moves preserved inode, size, and mtime. Files at or below 8 MiB were additionally sha256-verified before and after: 81,489 files. **Zero failed moves.**
- The manifest records each original path, destination path, category, size, inode, mtime, and hash. Any file can be restored by reversing its manifest pair.

## 3. What remains in `misc/`

Approximately 55,819 root entries remain: 156 broken and 73 live symlinks, the `barn-batch-0012` commit-less git residue, machine-generated extensionless artifacts of families not selected in this pass (`.so`, `.dylib`, `.bin`, `.img`, `.qcow2`, `.slang`, `.slangp`, `.dat`, and legacy mixed names), and the 68 restored provenance objects.

Those remaining families were deliberately not moved: several can be build inputs or evidence, and the operator directive named extra/duplicate/placeholder material, not every remaining byte. A second bounded pass would be needed to classify them.

## 4. Ledger and reversal

- `memory/catch_log/QUARANTINE_LEDGER.json` has a `MISC_BARN_REORGANIZATION` entry with source, destination, byte count, manifest hash, law, and verification counts, plus a `LIVE_REFERENCED_PROVENANCE_OBJECTS_RESTORED` entry for the 68 returned files.
- Nothing was deleted. No symlink was followed or rewritten. No persona, card, or voice asset was touched.
- This is a **same-volume reorganization**, so it does not by itself increase free space. Reclaiming the ~13 GiB requires moving the barn folder to external storage, which remains an owner decision.

## 5.Verification

The claims gate and final reality gate receipts are recorded after commit. No move was reported as complete until inode/hash verification returned zero failures and the live-reference restore was confirmed.
