# MISC AUDIT — 2026-11-17 (supersedes `barn_misc_oversize_report.txt`)

**Method:** every item re-stat'ed live on 2026-11-17 (`lstat`: apparent vs
allocated (`st_blocks*512`), APFS birth + modification time, `file --mime-type`,
symlink liveness). Classification is rule-based with explicit rules below;
irreplaceable items carry a 🔒 **owner-hold** overlay so no bulk-approval can
ever touch them. Nothing in this report has been deleted — all dispositions
await owner sign-off (Quarantine Law §10.5).

**Scope:** the 82 oversize items (≥50 MB) previously catalogued in
`barn_misc_oversize_report.txt`, plus the `misc/` symlink population.

## 1. Headline numbers

| Metric | Value |
|---|---|
| Oversize items in scope | 82 (79 present, 3 missing — Finding 1) |
| Total allocated (real disk) | **24.73 GB** |
| Total apparent | 285.22 GB (dominated by sparse `Docker.raw`: 245 GB apparent) |
| `misc/` total (all 137,122 items) | 33 GB allocated |
| Symlinks in `misc/` | 229 (156 broken, 73 alive) |
| Safe-reclaim pool (A+C+D, no owner-hold) | **8.26 GB** |
| Owner-hold (🔒 irreplaceable) | **16.10 GB** across 20 items |

## 2. Class totals and reconciliation with the earlier draft

| Class | Meaning | Items | Allocated | Reclaimable now? |
|---|---|---|---|---|
| **A** | verified byte-identical duplicate (`cmp`-proven) | 2 | 0.363 GB | ONE copy = **0.18 GB** (the pair is identical) |
| **C** | tooling / installers / caches / ML weights — re-downloadable | 65 | 22.609 GB | only the 45 non-hold items (see §3) |
| **D** | dead junk: partials, temp, orphaned downloads | 4 | 0.358 GB | **yes — recommended** |
| **E** | video files — human review first | 8 | 1.396 GB | only after review (3 are 🔒 personal recordings) |
| **GONE** | present in the stale report, missing today | 3 | 0 (was ~2.65 GB apparent) | Finding 1 |

**Reconciliation with the earlier recorded draft totals (A 0.18 / C 7.57 /
D 5.72 / E 1.87 GB):**

- **A matches exactly** — 0.18 GB = one copy of the `update.zip` ≡
  `Antigravity.zip` pair (byte-identical, `cmp`-verified).
- The earlier draft placed **`xoras.db` (4.17 GB) inside Class D** and
  `disk.qcow2` (0.80 GB) inside Class C. Both are irreplaceable owner state.
  This report moves them to 🔒 **owner-hold**, so an "approve Class D"
  decision **cannot delete `xoras.db`**. This is the single most important
  change since the draft.
- The earlier draft counted the personal `.mov` recordings (1.03 GB) and
  `QtWebEngineCore` (0.47 GB) in Class E; the `.mov`s are now 🔒 owner-hold.
- Small remaining deltas are boundary reclassifications (junk regexes);
  every item is individually listed in §4 with its current class.

## 3. Reclaim ladder (for the disk decision — 14B model needs ~15 GB, free 8.2 GB)

| Step | What | Gain | Risk |
|---|---|---|---|
| 1 | Class D dead junk (4 items: `_partial`, `CFNetworkDownload_*.tmp`, `uninstall`, `PFSceneGeographyData.index`) | 0.36 GB | none — dead files |
| 2 | Class A one copy of the identical zip pair | 0.18 GB | none — twin kept |
| 3 | Class C re-downloadable tooling (45 non-hold items: installers, app zips, binaries, ML weights, content-addressed blobs) | 7.72 GB | re-download required later |
| **Total** | | **8.26 GB** → ~16.5 GB free | funds the 14B model pull |

Owner-hold 🔒 items are excluded from every step above.

## 4. Full item table (82 rows)

| # | Class | Hold | File | Allocated | Apparent | Birth | Modified | Kind | State | Purpose / disposition |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **C** | 🔒 | `Docker.raw` | 4.94 GB | 245.11 GB | 2026-10-04 | 2026-10-12 | file/octet-stream | present | VM/disk image — irreplaceable state |
| 2 | **C** | 🔒 | `xoras.db` | 4.17 GB | 4.17 GB | 2026-06-17 | 2026-07-29 | file/vnd.sqlite3 | present | state/agent-history DB — irreplaceable |
| 3 | **C** | 🔒 | `disk` | 1.15 GB | 21.47 GB | 2026-08-20 | 2026-10-04 | file/octet-stream | present | VM/disk image — irreplaceable state |
| 4 | **C** | 🔒 | `disk.qcow2` | 803.0 MB | 803.0 MB | 2026-05-07 | 2026-05-07 | file/octet-stream | present | VM/disk image — irreplaceable state |
| 5 | **C** | 🔒 | `desktop.img` | 677.0 MB | 677.0 MB | 2026-08-29 | 2026-10-12 | file/octet-stream | present | VM/disk image — irreplaceable state |
| 6 | **C** | 🔒 | `483e85da-5758-4fb1-bd2d-074ab1d648d1.db` | 659.3 MB | 659.3 MB | 2026-09-04 | 2026-09-14 | file/vnd.sqlite3 | present | agent-trajectory DB — irreplaceable |
| 7 | **C** | 🔒 | `8cd1379f-71fa-4206-987a-23b5dfdc2254.db` | 638.8 MB | 638.8 MB | 2026-08-08 | 2026-09-04 | file/vnd.sqlite3 | present | agent-trajectory DB — irreplaceable |
| 8 | **C** | 🔒 | `7e14740c-2a12-4651-833e-e0b629519b95.db` | 467.9 MB | 467.9 MB | 2026-09-15 | 2026-09-18 | file/vnd.sqlite3 | present | agent-trajectory DB — irreplaceable |
| 9 | **C** | 🔒 | `71a8ce2b-da4e-4958-855b-219e4933386c.db` | 395.1 MB | 395.1 MB | 2026-10-07 | 2026-10-07 | file/vnd.sqlite3 | present | agent-trajectory DB — irreplaceable |
| 10 | **C** | 🔒 | `kokoro-v1_0.onnx` | 325.5 MB | 325.5 MB | 2026-09-17 | 2026-09-17 | file/octet-stream | present | Kokoro voice model — STAYS (speech pipeline) |
| 11 | **C** | 🔒 | `f00615a7-7fcc-4753-91b8-eeca487c6701.db` | 220.1 MB | 220.1 MB | 2026-08-29 | 2026-09-06 | file/vnd.sqlite3 | present | agent-trajectory DB — irreplaceable |
| 12 | **C** | 🔒 | `codebase-external.sqlite` | 155.5 MB | 155.5 MB | 2026-09-12 | 2026-09-12 | file/vnd.sqlite3 | present | state/agent-history DB — irreplaceable |
| 13 | **C** | 🔒 | `f64141ae-3cee-4028-9fa9-aedf81bdd2c5.db` | 144.4 MB | 144.4 MB | 2026-09-07 | 2026-09-07 | file/vnd.sqlite3 | present | agent-trajectory DB — irreplaceable |
| 14 | **C** | 🔒 | `f6a23b1f-c1f5-4021-ace4-0e1d3f424442.db` | 88.1 MB | 88.1 MB | 2026-09-04 | 2026-09-06 | file/vnd.sqlite3 | present | agent-trajectory DB — irreplaceable |
| 15 | **C** | 🔒 | `39bb973b-b12a-4695-a114-b90341f3b738.db` | 82.6 MB | 82.6 MB | 2026-09-04 | 2026-09-07 | file/vnd.sqlite3 | present | agent-trajectory DB — irreplaceable |
| 16 | **C** | 🔒 | `8d26e5d4-b8c6-4f10-b831-6d4382fe60b2.db` | 76.5 MB | 76.5 MB | 2026-09-28 | 2026-09-28 | file/vnd.sqlite3 | present | agent-trajectory DB — irreplaceable |
| 17 | **C** | 🔒 | `opencode.db` | 72.7 MB | 72.7 MB | 2026-07-08 | 2026-08-29 | file/vnd.sqlite3 | present | state/agent-history DB — irreplaceable |
| 18 | **E** | 🔒 | `C7AD3D0A-7EDF-412C-A237-B3C9D27381A1.mov` | 598.5 MB | 598.5 MB | 2026-10-12 | 2026-10-12 | file/quicktime | present | personal screen recording — irreplaceable |
| 19 | **E** | 🔒 | `EC3DC957-D4C2-4732-AACE-7D0C0F390EC8.mov` | 300.5 MB | 300.5 MB | 2026-10-12 | 2026-10-12 | file/quicktime | present | personal screen recording — irreplaceable |
| 20 | **E** | 🔒 | `8C31B06F-91A4-4F7C-93ED-56146D7F48B9.mov` | 130.1 MB | 130.1 MB | 2026-10-12 | 2026-10-12 | file/quicktime | present | personal screen recording — irreplaceable |
| 21 | **A** |  | `update.zip` | 181.6 MB | 181.6 MB | 2026-10-01 | 2026-10-12 | file/zip | present | cmp-verified byte-identical twin — reclaim ONE copy |
| 22 | **A** |  | `Antigravity.zip` | 181.6 MB | 181.6 MB | 2026-10-09 | 2026-10-09 | file/zip | present | cmp-verified byte-identical twin — reclaim ONE copy |
| 23 | **C** |  | `e2420b0a1de6ace6d539ff205ca65a2582d446f96971b9b8bc344dc6` | 757.3 MB | 757.3 MB | 2026-10-06 | 2026-10-06 | file/x-chrome-extensi | present | content-addressed blob (Ollama/cache) |
| 24 | **C** |  | `QtWebEngineCore` | 467.7 MB | 467.7 MB | 2026-03-31 | 2026-03-31 | file/x-mach-binary | present | tooling/cache artifact — re-downloadable |
| 25 | **C** |  | `github` | 422.7 MB | 422.7 MB | 2026-10-06 | 2026-10-06 | file/x-mach-binary | present | standalone binary — re-downloadable |
| 26 | **C** |  | `72db1f2b-a5b1-4ec0-956e-02c545d218cc.pb` | 384.8 MB | 384.8 MB | 2026-10-11 | 2026-10-11 | file/octet-stream | present | content-addressed blob (Ollama/cache) |
| 27 | **C** |  | `429fcd1f183390be9964682c4f151dc5977489f1e427d2540fff7d60` | 366.4 MB | 366.4 MB | 2026-02-25 | 2026-02-25 | file/gzip | present | installer/archive — re-downloadable |
| 28 | **C** |  | `model.gguf` | 274.3 MB | 274.3 MB | 2026-05-20 | 2026-05-20 | file/octet-stream | present | ML weight — re-downloadable |
| 29 | **C** |  | `Google Chrome for Testing Framework` | 246.1 MB | 246.1 MB | 2026-10-09 | 2026-10-09 | file/x-mach-binary | present | tooling/cache artifact — re-downloadable |
| 30 | **C** |  | `Telegram` | 234.7 MB | 234.7 MB | 2026-10-08 | 2026-10-08 | file/x-mach-binary | present | tooling/cache artifact — re-downloadable |
| 31 | **C** |  | `gradle-8.14-all.zip` | 224.1 MB | 224.1 MB | 2026-05-04 | 2026-05-04 | file/zip | present | installer/archive — re-downloadable |
| 32 | **C** |  | `com.docker.backend` | 220.9 MB | 220.9 MB | 2026-08-29 | 2026-10-12 | file/x-mach-binary | present | tooling/cache artifact — re-downloadable |
| 33 | **C** |  | `semgrep-core` | 209.8 MB | 209.8 MB | 2026-09-08 | 2026-09-08 | file/x-mach-binary | present | standalone binary — re-downloadable |
| 34 | **C** |  | `2.1.248` | 206.5 MB | 206.5 MB | 2026-08-27 | 2026-08-27 | file/x-mach-binary | present | standalone binary — re-downloadable |
| 35 | **C** |  | `agy` | 176.6 MB | 176.6 MB | 2026-10-06 | 2026-10-06 | file/x-mach-binary | present | standalone binary — re-downloadable |
| 36 | **C** |  | `p2a_dual_prompt_encoder_7e661f6b-b803-4b63-8510-6bde7f12` | 159.4 MB | 159.4 MB | 2026-09-17 | 2026-09-17 | file/octet-stream | present | content-addressed blob (Ollama/cache) |
| 37 | **C** |  | `p2a_single_prompt_decoder_prompt_extraction_5c9111ea-de6` | 150.7 MB | 150.7 MB | 2026-09-17 | 2026-09-17 | file/octet-stream | present | content-addressed blob (Ollama/cache) |
| 38 | **C** |  | `Telegram.app.zip` | 150.4 MB | 150.4 MB | 2026-10-08 | 2026-10-08 | file/zip | present | installer/archive — re-downloadable |
| 39 | **C** |  | `rnnt_encode_chunks_quantized_dynamic.onnx` | 150.3 MB | 150.3 MB | 2025-10-23 | 2025-10-23 | file/octet-stream | present | ML weight — re-downloadable |
| 40 | **C** |  | `node` | 145.8 MB | 145.8 MB | 2026-09-09 | 2026-09-09 | file/x-mach-binary | present | standalone binary — re-downloadable |
| 41 | **C** |  | `opencode` | 135.1 MB | 135.1 MB | 2026-07-08 | 2026-07-08 | file/x-mach-binary | present | standalone binary — re-downloadable |
| 42 | **C** |  | `66a93d64-59e1-45e5-b7a4-d7ed8d8409a2.pb` | 130.7 MB | 130.7 MB | 2026-09-19 | 2026-09-19 | file/octet-stream | present | content-addressed blob (Ollama/cache) |
| 43 | **C** |  | `Notion-arm64-7.37.1.zip` | 125.0 MB | 125.0 MB | 2026-10-07 | 2026-10-07 | file/zip | present | installer/archive — re-downloadable |
| 44 | **C** |  | `5ab971e21445d931203ebb75444e9917d67a2375fd726b5492c0cb7b` | 121.8 MB | 121.8 MB | 2026-09-16 | 2026-09-16 | file/x-mach-binary | present | content-addressed blob (Ollama/cache) |
| 45 | **C** |  | `2a222b221162f81eb412d8b4a0281edae48ede6093323b2b5ce5ca06` | 121.5 MB | 121.5 MB | 2026-07-08 | 2026-07-08 | file/x-mach-binary | present | content-addressed blob (Ollama/cache) |
| 46 | **C** |  | `Notion-arm64-7.31.0.zip` | 121.0 MB | 121.0 MB | 2026-08-22 | 2026-08-22 | file/zip | present | installer/archive — re-downloadable |
| 47 | **C** |  | `p2a_single_prompt_encoder_d732ed7b-09f5-4b88-b9a6-ebb129` | 119.0 MB | 119.0 MB | 2026-09-11 | 2026-09-11 | file/octet-stream | present | content-addressed blob (Ollama/cache) |
| 48 | **C** |  | `p2a_single_prompt_encoder_6efd37c4-8488-4b39-8b4a-c54a1b` | 119.0 MB | 119.0 MB | 2026-08-30 | 2026-08-30 | file/octet-stream | present | content-addressed blob (Ollama/cache) |
| 49 | **C** |  | `p2a_single_prompt_encoder_2e4dceaf-107f-42a0-9b9f-a2095d` | 118.8 MB | 118.8 MB | 2026-09-17 | 2026-09-17 | file/octet-stream | present | content-addressed blob (Ollama/cache) |
| 50 | **C** |  | `Microsoft.AI.Foundry.Local.Core.dylib` | 104.8 MB | 104.8 MB | 2026-10-06 | 2026-10-06 | file/x-mach-binary | present | native library — app artifact, re-fetchable |
| 51 | **C** |  | `d63aae08f6f16c129c03f4ff5f35cccb8e7d9642fb2081d3385e1cc8` | 93.0 MB | 93.0 MB | 2026-08-20 | 2026-08-20 | file/gzip | present | content-addressed blob (Ollama/cache) |
| 52 | **C** |  | `789fdf16a3e59f4fbfb6002967ecee539a198dadb5be74ca549aa7dc` | 90.9 MB | 90.9 MB | 2026-10-04 | 2026-10-04 | file/octet-stream | present | content-addressed blob (Ollama/cache) |
| 53 | **C** |  | `libllvmlite.dylib` | 90.5 MB | 90.5 MB | 2026-07-05 | 2026-07-05 | file/x-mach-binary | present | native library — app artifact, re-fetchable |
| 54 | **C** |  | `TelegramShare` | 88.0 MB | 88.0 MB | 2026-10-08 | 2026-10-08 | file/x-mach-binary | present | tooling/cache artifact — re-downloadable |
| 55 | **C** |  | `file_service.darwin-universal.node` | 78.7 MB | 78.7 MB | 2026-10-01 | 2026-10-01 | file/x-mach-binary | present | native library — app artifact, re-fetchable |
| 56 | **C** |  | `pack-8e28219300d57c2bef2b1934cf72b00b0c96fb6f.pack` | 72.9 MB | 72.9 MB | 2026-09-12 | 2026-09-12 | file/x-git | present | content-addressed blob (Ollama/cache) |
| 57 | **C** |  | `forge` | 67.2 MB | 67.2 MB | 2026-05-08 | 2026-05-08 | file/x-mach-binary | present | standalone binary — re-downloadable |
| 58 | **C** |  | `p2a_single_prompt_decoder_fc2fec59-6357-4ba9-9ddc-1d28e3` | 63.9 MB | 63.9 MB | 2026-08-30 | 2026-08-30 | file/octet-stream | present | content-addressed blob (Ollama/cache) |
| 59 | **C** |  | `p2a_single_prompt_decoder_a558c8b0-3893-4d84-90fb-fe6720` | 63.9 MB | 63.9 MB | 2026-09-11 | 2026-09-11 | file/octet-stream | present | content-addressed blob (Ollama/cache) |
| 60 | **C** |  | `p2a_dual_prompt_decoder_c2bb0f32-edbe-464b-84ac-c66ac5a9` | 63.9 MB | 63.9 MB | 2026-06-25 | 2026-06-25 | file/octet-stream | present | content-addressed blob (Ollama/cache) |
| 61 | **C** |  | `p2a_dual_prompt_decoder_a228fb64-f3dc-4750-891e-bce18f22` | 63.9 MB | 63.9 MB | 2026-09-17 | 2026-09-17 | file/octet-stream | present | content-addressed blob (Ollama/cache) |
| 62 | **C** |  | `docker-buildx` | 63.4 MB | 63.4 MB | 2026-08-29 | 2026-10-12 | file/x-mach-binary | present | standalone binary — re-downloadable |
| 63 | **C** |  | `libxgrammar.a` | 63.2 MB | 63.2 MB | 2026-07-05 | 2026-07-05 | file/x-archive | present | native library — app artifact, re-fetchable |
| 64 | **C** |  | `906c2761507749121d204692ef5a82c30a1609cdca65d6810abba030` | 63.1 MB | 63.1 MB | 2026-08-09 | 2026-08-09 | file/gzip | present | installer/archive — re-downloadable |
| 65 | **C** |  | `codex-code-mode-host` | 62.8 MB | 62.8 MB | 2026-09-14 | 2026-09-14 | file/x-mach-binary | present | standalone binary — re-downloadable |
| 66 | **C** |  | `es-MX_g2p_seq2seq.bin` | 61.6 MB | 65.4 MB | 2026-09-17 | 2026-09-17 | file/octet-stream | present | ML weight — re-downloadable |
| 67 | **C** |  | `kotlin-compiler-embeddable-2.0.21.jar` | 58.3 MB | 58.3 MB | 2026-05-04 | 2026-05-04 | file/zip | present | installer/archive — re-downloadable |
| 68 | **C** |  | `kubectl` | 57.3 MB | 57.3 MB | 2026-08-29 | 2026-10-12 | file/x-mach-binary | present | standalone binary — re-downloadable |
| 69 | **C** |  | `libchromescreenai.so` | 56.2 MB | 56.2 MB | 2026-10-01 | 2026-10-01 | file/x-mach-binary | present | native library — app artifact, re-fetchable |
| 70 | **C** |  | `a5f3cf26ff817a1304109acc59ddb0a620d4eba6fcd151dfd17c3595` | 52.5 MB | 52.5 MB | 2026-05-26 | 2026-05-26 | file/x-chrome-extensi | present | content-addressed blob (Ollama/cache) |
| 71 | **D** |  | `telegram-cloud-document-2-5217433620146332327_partial` | 138.9 MB | 138.9 MB | 2026-10-07 | 2026-10-07 | file/zip | present | dead junk / partial / orphaned — reclaim recommended |
| 72 | **D** |  | `PFSceneGeographyData.index` | 88.5 MB | 88.5 MB | 2026-05-27 | 2026-05-27 | file/octet-stream | present | dead junk / partial / orphaned — reclaim recommended |
| 73 | **D** |  | `CFNetworkDownload_HEb3nb.tmp` | 68.7 MB | 68.7 MB | 2026-09-17 | 2026-09-17 | file/quicktime | present | dead junk / partial / orphaned — reclaim recommended |
| 74 | **D** |  | `uninstall` | 61.5 MB | 61.5 MB | 2026-08-29 | 2026-10-12 | file/x-mach-binary | present | dead junk / partial / orphaned — reclaim recommended |
| 75 | **E** |  | `Daniel-in-the-Lions-Den-Film.mp4` | 112.8 MB | 112.8 MB | 2026-09-19 | 2026-09-19 | file/mp4 | present | video — human review before delete |
| 76 | **E** |  | `Architecting_the_Deterministic_Agent__From_Vectors_to_St` | 75.2 MB | 75.2 MB | 2026-09-23 | 2026-09-23 | file/mp4 | present | video — human review before delete |
| 77 | **E** |  | `Governing_the_Chaos.mp4` | 63.9 MB | 63.9 MB | 2026-09-23 | 2026-09-23 | file/mp4 | present | video — human review before delete |
| 78 | **E** |  | `The_Architecture_of_Machine_Cognition.mp4` | 61.1 MB | 61.1 MB | 2026-09-23 | 2026-09-23 | file/mp4 | present | video — human review before delete |
| 79 | **E** |  | `Fixing_AI_Context_Gap.mp4` | 53.6 MB | 53.6 MB | 2026-09-23 | 2026-09-23 | file/mp4 | present | video — human review before delete |
| 80 | **GONE** |  | `?` | 0.0 MB | 0.0 MB |  |  | /? | MISSING | Ollama model blob — gone entirely (Finding 1) |
| 81 | **GONE** |  | `?` | 0.0 MB | 0.0 MB |  |  | /? | MISSING | Ollama model blob — gone entirely (Finding 1) |
| 82 | **GONE** |  | `?` | 0.0 MB | 0.0 MB |  |  | /? | MISSING | Ollama model blob — gone entirely (Finding 1) |


## 5. Symlink findings

- 229 symlinks total in `misc/`: **156 broken** (target gone), 73 alive.
- The broken population dates from the Oct 26 22:38–22:44 symlink creation
  wave pointing at `databases_and_ledgers/` (see §6); their targets were
  removed when that directory was emptied on Nov 13.

## 6. Five agent-history DBs — loss timeline (forensics complete)

1. **Oct 23** — AppleDouble `._<UUID>` files at the USB root prove the five
   DBs existed there.
2. **Oct 26 22:38–22:44** — symlinks into `databases_and_ledgers/` created.
3. **Nov 13 04:15** — `databases_and_ledgers/` emptied; the same minute shows
   `GA_Backup/brain` modification — one process, one event.
4. **Nov 16** — v2 move manifest: **0 moved / 97 failed (Errno 5)**, all
   locals kept (`barn_misc_oversize_moves_20261117.json`,
   `scratch/barn_usb_move.log`).
5. Internal full-disk sweep: no APFS data snapshots, USB `.Trashes` empty,
   `~/.Trash` empty, real bytes (~4.84 GB) found nowhere short of disk
   carving. 390 small DBs (2.0 GB) remain intact in
   `categorized_corpus/databases_and_ledgers/`.

## 7. Finding 1 — three Ollama blobs vanished without a ledger entry

The stale report listed `sha256-41926ed5…` (1.20 GB), `sha256-29d8c98f…`
(0.99 GB), `sha256-6326fb9f…` (0.46 GB). Today all three are **missing**.
Provenance checks:

- NOT in `barn_misc_oversize_moves_20261117.json` (the 97-failure move log)
- NOT in `scratch/barn_usb_move.log` or `barn_misc_push.log`
- NOT in `QUARANTINE_LEDGER.json`
- NOT in `~/.ollama/models/blobs` (13 blobs, 5.6 GB — none match)
- The surviving sidecar `data/sha256-41926ed5….json` (born Sep 27) identifies
  them as **Ollama model weights** (Gemma 4 26B vision encoder metadata)

**Assessment:** re-downloadable model weights for a replaced model, not
unique data. Likely Ollama GC during model housekeeping — but there is no
receipt for their removal, which is itself a governance gap: a deletion
happened outside the ledger. Logged here as the record.

## 8. Correction to `barn_misc_oversize_report.txt`

That file (Nov 16 19:31) is a raw size-ordered listing and is **stale**: it
lists the three GONE blobs as present, predates the owner-hold overlay, and
carries no classification. This report supersedes it. Per §10.5 the stale
file is kept (nothing deleted), with this correction attached.

## 9. Open owner decisions

1. **Reclaim ladder §3** (8.26 GB) — approves the 14B model pull toward the
   20/25 golden floor. Steps 1–2 are zero-risk; step 3 needs re-download
   acceptance.
2. **Disk carving** for the five agent-history DBs (~4.84 GB, write target =
   the failing USB) — approve or write off.
3. **USB repair/replacement** before any new barn writes.
4. 🔒 owner-hold items (20): keep in place, move to USB after repair, or
   review individually.
