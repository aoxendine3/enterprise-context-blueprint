# Claim Validation — 2026-11-19

Deep validation of the claims in the pasted "full ceiling / honesty verification"
reports. Method: re-read the actual receipts/logs, recompute hashes, verify the
Ed25519 signature independently, rerun the gates, and search for named evidence
files across the repo and `/Users/ajoxendine68/Desktop/test/`.

## Verdict: the engineering numbers are real; the "honesty report" wrapper is not

### VERIFIED (backed by files this session re-checked)

| Claim | Evidence |
|---|---|
| v2 master receipt exists | `memory/catch_log/FULL_CEILING_BENCHMARK_RECEIPT_20261118.json`; file sha256 = `93dae1853cf4c3a81fb390500c1a7ccfc4beba1e9cdc0a57b4bcc967982d6f7e` |
| Canonical-JSON payload digest | `9bedc777f84a64c0` — computed over the signed payload, not the receipt file |
| Receipt is Ed25519-signed | independent verification with the receipt's own public key **VERIFIES** against the **canonical JSON payload** (128-hex signature) |
| Reality gate 9/9 | reproduced this session: `REALITY_GATE_PASS`, 9/9 at `2026-11-19T15:25:28Z` |
| Golden 24/25 = 96.0%, mean 97.12%, 0 forbidden | reproduced independently at `06:03:54Z` with `xoras-golden:latest` |
| v2 upload pack specs | PNGs 1600x900 RGB; MP4 1920x1080 H.264 High/yuv420p/30 fps/14 s; Option A = 278 chars (≤280) |
| Rust AST numbers (79,302 scans/s 1-core; 10-core scaling; 0/500,000 false negatives; 26/26 parity) | `scratch/full_ceiling_20261118/arthur_rust_10core.json` |
| Swarm numbers (4.3k→26.7k tx/s, 2.5 ms p99, 0 leaks) | `scratch/full_ceiling_20261118/rust_ffi_swarm_comparison.json` |
| Live model overhead 0.031%, mean turn 1556.16 ms | `scratch/full_ceiling_20261118/live_ollama_vs_rust_gate.json` |
| Linux seccomp 11/11 `EPERM`, `PASSED_PRE_WALL` | `scratch/full_ceiling_20261118/linux_container_proof.log` — 11 vector lines with `ret=-1, errno=1, eperm_blocked=true` |
| Zig Merkle root | present in the signed v2 payload and other receipts |

### FALSE / MISLEADING in the "honesty report" wrapper

| Claim | Finding |
|---|---|
| Evidence-file hash table | **Every checked file hash mismatches.** The listed prefixes were not the SHA-256 of the files. `9bedc777f84a64c0` is the canonical-JSON payload digest, not a receipt-file hash. Recomputed file hashes: benchmark receipt `93dae1853cf4c3a81fb390500c1a7ccfc4beba1e9cdc0a57b4bcc967982d6f7e`, reality receipt `cc040b96fc26a7576140e5cfaa511aa796e3005424766248c13ef6fd3f6f6cd4`, golden `967f27d25c58e004d2dd66cd82c005a7b022878ae8cc2b916ebc2f8c7b1c8f00`, seccomp log `d687bf53beaeb438efedf9832eea8c640fd1415d0cc10c209e619d61d40a6d19`, swarm JSON `c707a8cfd123402898a6cc3b4a670460f92bc097f298170ad671a814ea5f15f4`. |
| Named standalone evidence logs (shm_performance.log and m4_hardware_bandwidth_audit.log) | Do not exist anywhere in the repo or /Users/ajoxendine68/Desktop/test. The headline numbers live only inside the signed v2 payload, not in any standalone log. |
| Benchmark deliberation delay | The wrapper claimed the benchmark introduced no deliberation delay — **false**. The benchmark scripts call time.sleep(0.0001 + (tx % 3) * 0.0001), a deliberate 100-300 µs wait. |
| Signed timestamp | The wrapper claimed the signature timestamp was 2026-11-18 10:12 UTC — **false**. The v2 payload timestamp is 2026-11-19T05:23:35Z; the reality receipts are all dated 2026-11-19. |
| Unit test coverage claim | The wrapper claimed one hundred percent unit test coverage — **false**. No such gate exists; the cockpit floor is 80% line coverage. |
| Hallucination claim | Overstated. The golden receipt shows argument hallucination at 54.0%; zero forbidden hits is not zero hallucination. |
| 96% groundedness claim | The figure proves faithful reproduction, not independent reasoning. The harness instructs verbatim copying of supplied authority and answer at temperature 0.0; the scorer and floor were untouched. |
| Atlas AST gate | No such component. The real gates are arthur_ast_rs (Rust) and ASTSecurityEngine (Python). |
| Capstone trace | A simulation. No dataset, RFC, seccomp source, or capstone IDs were found in any receipt. |

### PARTIALLY VERIFIED / CAVEATS

- **Ed25519 signature**: valid, but it signs the canonical JSON payload — not the hash string or the file as the honesty claim implies. Verification with the declared key succeeds only for canonical JSON.
- **Reality gate stability**: the cockpit step failed on the first of two recent runs and passed on retry; standalone `ops/scripts/verify_cockpit.sh` always passes. A flaky test is a reliability defect to fix, not a fake result.
- **Native Rust path**: now promoted after a three-round independent audit (`memory/catch_log/AST_FFI_AUDIT_20261119.md`), but remains opt-in; the .dylib is gitignored, so fresh hosts must build it. Absent library now raises instead of degrading.

## Bottom line

The benchmarks and gates are genuine, signed, and reproducible. The
"honesty verification" wrapper around them contains fabricated file hashes,
two nonexistent evidence files, a false "no deliberation delay" assertion, and a
wrong timestamp. Trust the receipts; distrust the wrapper.
