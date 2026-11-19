# Claim Validation — 2026-11-19

Deep validation of the claims in the pasted "full ceiling / honesty verification"
reports. Method: re-read the actual receipts/logs, recompute hashes, verify the
Ed25519 signature independently, rerun the gates, and search for named evidence
files across the repo and `/Users/ajoxendine68/Desktop/test/`.

## Verdict: the engineering numbers are real; the "honesty report" wrapper is not

### VERIFIED (backed by files this session re-checked)

| Claim | Evidence |
|---|---|
| v2 master receipt exists, payload digest `9bedc777f84a64c0…` | `FULL_CEILING_BENCHMARK_RECEIPT_20261118.json`; canonical-JSON SHA-256 recomputed = `9bedc777…` |
| Receipt is Ed25519-signed | independent verification with the receipt's own public key **VERIFIES** against the **canonical JSON payload** (128-hex signature) |
| Reality gate 9/9 | reproduced this session: `REALITY_GATE_PASS`, 9/9 at `2026-11-19T15:25:28Z` |
| Golden 24/25 = 96.0%, mean 97.12%, 0 forbidden | reproduced independently at `06:03:54Z` with `xoras-golden:latest` |
| v2 upload pack specs | PNGs 1600×900 RGB; MP4 1920×1080 H.264 High/yuv420p/30 fps/14 s; Option A = 278 chars (≤280) |
| Rust AST numbers (79,302 scans/s 1-core; 10-core scaling; 0/500,000 false negatives; 26/26 parity) | `scratch/full_ceiling_20261118/arthur_rust_10core.json`, `arthur_native_parity_receipt.json` |
| Swarm numbers (4.3k→26.7k tx/s, 2.5 ms p99, 0 leaks) | `scratch/full_ceiling_20261118/rust_ffi_swarm_comparison.json` |
| Live model overhead 0.031%, mean turn 1556.16 ms | `scratch/full_ceiling_20261118/live_ollama_vs_rust_gate.json` |
| Linux seccomp 11/11 `EPERM`, `PASSED_PRE_WALL` | `scratch/full_ceiling_20261118/linux_container_proof.log` — 11 vector lines with `ret=-1, errno=1, eperm_blocked=true` |
| Zig Merkle root `c26b3d7301cc0…` | present in the signed v2 payload and other receipts |

### FALSE / MISLEADING in the "honesty report" wrapper

| Claim | Finding |
|---|---|
| Evidence-file hash table (`a4f2c1b9…`, `d3e9a6c2…`, `5f2e1a8c…`, `c7b9d4e1…`, `8a1d3f6b…`, `e4b2c7d9…`, `9bedc777…` as *file* hashes) | **Every checked file hash mismatches.** The listed prefixes are not the SHA-256 of the files. `9bedc777…` is the *payload digest*, not the receipt-file hash (actual `93dae185…`). Actual: reality receipt `4ffeca12…`, golden `967f27d2…`, seccomp log `d687bf53…`, swarm JSON `c707a8cf…`. |
| Named evidence `shm_performance.log` and `m4_hardware_bandwidth_audit.log` | **Do not exist** anywhere in the repo or Desktop/test (full search). The 8.22M ops/s and 37–40 GB/s numbers live only inside the signed v2 payload, not in the named standalone logs. |
| "No mock data or synthetic delays were used" | **False as written.** `bench_rust_ffi_swarm.py:88-89` and `run_full_ceiling.py:391-392` contain `time.sleep(0.0001 + (tx % 3)*0.0001)` — a synthetic 100–300 µs deliberation wait. The receipts disclose it; the honesty claim contradicts it. |
| "Signed timestamps match 2026-11-18 10:12 UTC" | **False.** v2 payload timestamp = `2026-11-19T05:23:35Z`; reality receipts are all 2026-11-19. |
| "100% unit test coverage" | **No such gate.** The cockpit floor is 80% line coverage (`verify_cockpit.sh:29-32`); actual last run 95.42%. |
| "Zero hallucination" | Overstated. Golden receipt simultaneously shows `arg-hallucination 54.0%`; the metric is "zero *forbidden* hits under a rule-based floor", not zero hallucination. |
| "96% proves reasoning" | No. The harness instructs verbatim copying of supplied authority + answer at temperature 0.0; it measures faithful reproduction. Scorer/floor untouched. |
| "Atlas AST gate" | No such component; real gates are `arthur_ast_rs` (Rust) and `ASTSecurityEngine` (Python). |
| "CAPSTONE_VERIFIED_PASS" multi-agent trace | Simulation. No dataset, RFC, seccomp source, or capstone IDs found in any receipt. |

### PARTIALLY VERIFIED / CAVEATS

- **Ed25519 signature**: valid, but it signs the canonical JSON payload — not the
  hash string or the file as the honesty claim implies. Verification with the
  declared key succeeds only for canonical JSON.
- **Reality gate stability**: the cockpit step failed on the first of two recent
  runs and passed on retry; standalone `verify_cockpit.sh` always passes. A
  flaky test is a reliability defect to fix, not a fake result.
- **Native Rust path**: now promoted after a three-round independent audit
  (`AST_FFI_AUDIT_20261119.md`), but remains opt-in; the `.dylib` is gitignored,
  so fresh hosts must build it. Absent library now raises instead of degrading.

## Bottom line

The benchmarks and gates are genuine, signed, and reproducible. The
"honesty verification" wrapper around them contains fabricated file hashes,
two nonexistent evidence files, a false "no synthetic delays" assertion, and a
wrong timestamp. Trust the receipts; distrust the wrapper.
