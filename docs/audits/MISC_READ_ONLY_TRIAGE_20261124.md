# `misc/` Read-Only Triage — 2026-11-24

**Status:** MEASURED, NO CHANGES. Every operation in this report was read-only (`du`, `stat`, `lsof`, `sqlite3?mode=ro&immutable=1`, bounded `grep`). Nothing in `misc/` was moved, deleted, renamed, or re-written.

**Owner-gated:** any archive move, deletion, or reclassification still requires explicit approval. This document is a decision input only.

## 1. Shape of the directory

| Measure | Value |
| :--- | :--- |
| Apparent size | 268.10 GiB (`os.lstat` sum) |
| Actual allocated space | **25.71 GiB** (`du`) |
| Files / dirs / symlinks | 137,136 / 16 / 229 |
| Root entries | 137,326 — the directory link count is saturated at 65,535 |
| Extensionless files | 106,559 (25.10 GiB apparent; names like `*.chunk`, `*.relevancecache`, `0.index*`) |
| Nested git | `misc/.git`, branch `barn-batch-0012`, **no commits**, ~137k `AD` index entries |

The apparent-vs-allocated gap is sparse allocation in the disk images, not missing data. The saturated root entry count is a structural problem: creating new files directly in `misc/` is unreliable.

## 2. The three large objects

| Path | Apparent | Allocated | Provenance / evidence |
| :--- | :--- | :--- | :--- |
| `misc/Docker.raw` | 245.11 GB | **4.60 GiB** | DOS/MBR Docker virtual disk. Same apparent size as the live Docker Desktop disk at `~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw`, but this copy's mtime is 2026-10-12 vs 2026-11-20 on the live file. `lsof` found no holder. |
| `misc/disk` | 21.47 GB | **1.07 GiB** | DOS/MBR/GPT virtual disk image, mtime 2026-10-04, birth 2026-08-20. `lsof` found no holder. |
| `misc/xoras.db` | 4.17 GB | **3.88 GiB** | SQLite 3, last written 2026-07-29. Read-only query: 1 project, 4 conversations, 345 messages, 1 settings row, 33,184 system metrics, 5,084 anomalies. Referenced by `workspaces/xoras-app/README.md` as the app's WAL store; `lsof` found no live holder. |

Allocated subtotal of these three: **9.55 GiB**. `misc/.git` adds **0.45 GiB**. The remaining **~15.71 GiB** is spread across the 137k small cache/index files at the root level.

## 3. Live-reference sweep (bounded, outside `misc/`)

- `Docker.raw` — only `docs/docker_storage_and_container_content_report.md` (historical report about Docker Desktop's own disk).
- `xoras.db` — only `workspaces/xoras-app/README.md` (architecture description).
- `misc/disk` — no reference outside `misc/`.
- `lsof` on all three returned no open handles.

This is a reference check, not proof that the data is worthless. The Docker image may still contain model weights and container layers described in the 2026-11-18-era report; the database may hold historical conversations. Only the operator can decide their value.

## 4. Recommendations — NOT executed

1. **Do not delete anything.** Preserve by moving intact, with sha256 and a quarantine/ledger entry.
2. **Highest-value, lowest-risk archive candidates:** `misc/Docker.raw` (4.60 GiB), `misc/xoras.db` (3.88 GiB), `misc/disk` (1.07 GiB) — about **9.55 GiB** reclaimed if moved to external storage or The Barn after hash verification.
3. **The 15.71 GiB of cache/index files is the real bulk.** It should be inventoried by generator before any move; the `*.chunk` / `*.relevancecache` / `0.index*` families look machine-generated, but no owner-approved provenance exists.
4. **`misc/.git` has no commits and a 137k-entry `AD` index.** Do not repair it in place. If the batch was already preserved elsewhere, archive the whole `.git` intact rather than rebuilding history.
5. **Disk context:** volume is 190 GiB used / 11 GiB free (95%). Reclaiming ~9.5 GiB would roughly double the free space. Do not use `docker builder prune -a` from the old report — Docker Desktop's daemon is currently unusable and its disk is not the copy in `misc/`.

## 5. What we need from the owner

- Confirm which of the three large objects may be archived off this volume.
- Name the external destination (USB source / The Barn) for hash-verified moves.
- State whether the historical `xoras.db` conversations must stay online.
- Approve or reject an inventory-by-generator pass over the 137k cache files.

No move, deletion, token rotation, push, or lineage change was performed as part of this triage.
