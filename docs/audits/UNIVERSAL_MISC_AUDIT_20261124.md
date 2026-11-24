# Universal Audit of `misc/` — 2026-11-24

**Status:** MEASURED AND VERIFIED — read-only. No file in `misc/` was moved, deleted, renamed, or rewritten.
**Authority:** owner-gated. Archival moves, deletions, and credential rotation remain with the operator.
**Method:** the repository's own scanners were called directly against `misc/`, with hard read bounds. Scanner defaults were not weakened; the tools that exclude `misc/` by design were invoked on it explicitly so the exclusion could be measured rather than assumed.

## 1. Scope and bounds

| Pass | Tool / mechanism | Bound |
| :--- | :--- | :--- |
| Inventory | `os.lstat` walk, no file opens | 137,096 files |
| Content class | magic-byte classifier | 2,000 deterministic samples, 16-byte head read |
| AST symbols | `ops/scripts/multi_lang_ast_parser.py::scan_symbol_equivalence` | whole `misc/` tree |
| Taint | `ops/scripts/daxx_ast_taint_live_scanner.py::SemanticASTTaintScanner` | Python files only (0 exist) |
| Credentials | `ops/scripts/deep_credential_audit.py::PATTERNS` | 2,016 text/sample files, 2 MB per-file cap |
| Provenance gate | `ops/scripts/preflight_data_classifier.py::classify_dataset` | 200 deterministic samples |
| Context search | `core/ops/scripts/dual_plane_search.py` (temporal plane) | two queries, bounded git pickaxe |
| Archive integrity | sha256 over all 3,076 manifest entries | 55.6 MB of indexed files |
| Symlinks | `os.path.islink` + `os.path.exists` | whole tree |

Machine-readable evidence is at `memory/catch_log/UNIVERSAL_MISC_AUDIT_RECEIPT_20261124.json` (schema `xoras.universal_misc_audit.v1`, 37.05 s), mirrored from the run output. The harness is `scratch/universal_misc_audit_20261124.py`.

## 2. What is actually in `misc/`

- **137,096 files**, 25.71 GiB allocated, 268.10 GiB apparent (sparse disk images).
- **106,536 extensionless files.** Of these, **62,259** follow the Chrome cache-data naming form `hex16_N` — the dominant content family. Another 484 use MD5-like 32-hex names; 611 are purely numeric; 43,356 are mixed legacy artifacts, including nvm test fixtures with names such as `"nvm alias" should not accept aliases with slashes`.
- Other large families: 7,110 `.pyc`, 5,588 `.map`, 2,426 `.o`, 641 `.slangp`, 604 `.slang`, 557 `.journal`, 548 `.so`, 535 `.meta`, 522 `.plist`, 479 `.gemspec`, 459 `.mts`.
- **Only 16 code-ish files** and **zero Python sources** exist here. The rest is cache, compiled objects, and image blobs.
- Magic-byte sample (2,000 files): 1,268 opaque binary, 678 UTF-8 text, 24 gzip, 7 DOS executables, 7 ZIP, 5 SQLite, 5 PNG, 2 shebang scripts, 1 WASM, 1 PDF, 1 RIFF, 1 Ogg.

**Conclusion:** `misc/` is predominantly browser-cache spill and build-artifact debris, not a source tree. That is why the codebase scanners find nothing to parse there.

## 3. What the tools found

### 3.1 AST / taint — zero targets, reported honestly

The AST symbol engine parsed **0 modules** and the taint engine traversed **0 modules / 0 AST nodes / 0 sinks**. Both are true zeros from a real invocation, not skipped gates: there are no `.py` files in `misc/`.

### 3.2 Credential scan — six pattern hits, all in cache blobs

Six regex matches were found across five files. Each was re-read with byte-level context and redacted before reporting. **None is a confirmed live credential.**

| File (Chrome-cache form) | Pattern | Evidence after inspection |
| :--- | :--- | :--- |
| `misc/c662a4094d33a4aa_0` | google_api_key | Embedded in a cached Google omnibox `sugkey=` URL; Google's public suggest key, not owner secret |
| `misc/1930a0ba3a194783_0` | google_api_key | Same cached omnibox `sugkey=` URL form |
| `misc/29213d2ab33b53bc_0` | google_api_key (2) | Cached `mail.google.com` HTML; Google's own web-app key in page data |
| `misc/0ae129c33e7a30bd_0` | private_key_block | 17-byte literal `-----BEGIN PRIVATE KEY` inside minified JS PKCS#8 format-validation code — a string check, not a key body |
| `misc/55351860c95e6f10_0` | hf_token | 55-character `hf_`-prefixed run adjacent to a `JFIF` JPEG header in a binary cache blob; non-standard token length, byte coincidence in cached image data |

No rotation, redaction-in-place, or quarantine was performed. If the operator wants zero residual doubt, rotate the HuggingFace token only after confirming it in the live provider console; the other five are public Google patterns and a JS literal.

### 3.3 Provenance classifier — expected rejections, not failures

Of 200 sampled files: **61 REJECTED** (UTF-8 text without the mandatory `REAL_HARDWARE_TELEMETRY` / `SYNTHETIC_BENCHMARK` tag — correct for cache debris) and **139 ERROR** (binary files cannot be decoded as UTF-8 by that tool). Neither verdict means "malicious"; the classifier is designed for benchmark-dataset admission, and cache files were never candidate datasets.

### 3.4 Context / temporal search

`dual_plane_search.py` was used in its attested mode:

- Query `Docker.raw`: 6 historical pickaxe matches; structural plane reports `<index not built>` and bypass attestation, with a forced walk confirming the same five report files.
- Query `xoras.db`: 3 historical pickaxe matches; same bypass attestation.
- `misc/` is explicitly in the tool's `BYPASS_DIRS` list, so "no structural hits" is **never** silently trusted. The attestation is present in both receipts.

## 4. Provenance already on disk

- **52 repository files reference `misc/`**, including the barn batch manifests, the reclaim manifest, the coverage ledger, and three prior audits.
- **Batch 0012 is preserved.** Its manifest records 3,076 files with sha256 values and commit ID `0898593c8906c0ccc968e37a35e47e8a4e08e306` on branch `barn-batch-0012` against the `xoras-barn-misc` remote. The commit object is present locally and its tree contains exactly 3,076 entries. All 3,076 worktree paths are now absent from `misc/` — they were archived, **not lost**. The commit-less branch and `AD` index state are the residue of that move.
- **The 2026-11-19 reclaim is intact.** Its manifest records 54 hash-verified moves to the external volume; that volume is currently mounted and a sampled moved file is present on disk.
- **Symlinks:** 73 alive, **156 broken**. Broken examples point at removed node_modules bins and an old `xoras-core` checkout. These are dangling references, not data loss.

## 5. Largest objects (from the read-only triage)

| Object | Allocated | Disposition |
| :--- | :--- | :--- |
| `misc/Docker.raw` | 4.60 GiB | Stale copy of Docker Desktop disk; no live holder |
| `misc/xoras.db` | 3.88 GiB | Historical SQLite, 345 messages; no live holder |
| `misc/disk` | 1.07 GiB | Secondary virtual disk; no live holder |

The remaining ~15.71 GiB is distributed across the 137k cache/index files. Reclaiming the three large objects would roughly double free space, but every move remains owner-gated.

## 6. Verdict and owner decisions required

The universal audit finds **no source code, no active taint surface, no confirmed live credential exposure, and intact archival provenance**. The dominant content is browser cache and compiled artifacts. Nothing here justifies deleting `misc/` wholesale: the historical database, disk images, and archived-batch residue need an owner value judgment.

Decisions still held for the operator:

1. Which of the three large objects may be hash-verified and moved off this volume.
2. Whether the historical `xoras.db` conversations must stay online.
3. Whether to rotate the HuggingFace token as a precaution.
4. Whether to sweep the 43,356 "other" extensionless legacy artifacts by generator.
5. Whether to prune the 156 broken symlinks (a wiring repair, not a data move).

## 7. Verification

The claims gate returned `CLAIMS_PASS` with zero hash-bound assertions; this report deliberately makes no hash claim that has not been recomputed above from live files. The final reality gate and its receipt are recorded after commit.

**No move, deletion, token rotation, push, or lineage change was performed as part of this audit.**
