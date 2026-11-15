# Scanner & Byzantine History Review — 2026-11-15

**Who:** build seat (DAXX standard), by direct inspection and execution on this host.
**What:** whether an AST scanner was built in Zig or Rust, and what the UPGP / dojo history actually contains on scanners and Byzantine swarms.
**Why:** an external reviewer asked how the council pipeline scales past 128 workers. The answer depends on whether a native scanner exists and whether the "Byzantine swarm" numbers describe consensus or vote-counting. Both needed checking against artifacts, not filenames.
**Method:** file inspection, native rebuild, execution, parity run against the adversarial corpus. No claim below is taken from a document without its artifact being located.
**Companion receipt:** `memory/catch_log/arthur_native_parity_receipt.json`

---

## 1. Was the scanner built in Zig or Rust?

**Rust. There is no Zig AST scanner.** One real Rust engine exists and it works.

### 1.1 `core/ops/src/arthur_ast_rs/` — real (Rust + tree-sitter-python)

- 455 lines in `src/lib.rs`; `tree-sitter 0.27.1`, `tree-sitter-python 0.25.0`.
- Implements a taint lattice (`ExternalPoison`, `SanitizedAntidote`, `Literal`, `Unknown`), denylisted calls/modules, dunder-attribute detection, and `if x in (whitelist)` antidote recognition.
- **Built natively today** (`cargo build --release`, 9.3 s). The committed `target/release/arthur_ast_rs` was **Linux x86_64** — it produced `exec format error` on this Mac, i.e. it had only ever been built inside Docker, never run natively.
- **Parity: 26/26** against the Python kernel (`ArthurSanitizerLatticeKernel.scan_python_ast_security`) on the four adversarial gauntlet corpora plus a benign control. No mismatches.
- **In-process cost: 14.36 µs/scan, 69,644 scans/s single core** (`bench_in_process`, 500,000 scans). Python equivalent measured at **196 µs/scan** → **13.7× faster**.

### 1.2 It is not wired into anything

- `CouncilOrchestrator.execute_governed_task` uses the Python `ASTSecurityEngine` — the 196 µs path.
- The only harness that invokes the Rust engine, `core/ops/scripts/run_exhaustive_arthur_parity_gauntlet.py`, shells out through **Docker** with a hardcoded `/workspace` mount. On this host it cannot run as written.
- Measured the deployed shape (subprocess per file): **2.33 ms median**, i.e. **12× slower than the Python scanner it would replace**. Process spawn dominates a 14 µs parse.
- Consequence: "move the gate to Rust" only helps if it is called **in-process (FFI/PyO3) or through a persistent daemon**. A CLI-per-file wiring is strictly worse than what we have.

### 1.3 Rust artifacts whose names overstate them

| Path | What it actually is | Verdict |
|---|---|---|
| `core/ops/src/xoras_ast_parser/` | TCP/UDP Ed25519 handshake daemon, 74 lines, hardcoded pubkey, binds UDP **11434** (Ollama's port). Parses no AST. | Misnamed; port conflict |
| `core/ops/src/crypto_swarm/` | Hashes one file 25,000,000× with rayon, counts non-zero first bytes. | Hash-throughput bench, not a swarm |
| `core/ops/mtpo_deeplock/` | 102-line saga/rollback lib | Accurate |

### 1.4 Zig: no AST scanner

- `core/ops/native/zig/sovra_truth_engine_v4.zig` — a tokenizer over text claims (`tokenizeAny`), not source AST.
- The Zig files with "byzantine" in the name (`max_byzantine_swarm.zig`, `byzantine_corruption_sweep.zig`) are vote counters, not scanners.

---

## 2. UPGP and dojo: scanners and Byzantine swarms

### 2.1 The dojo is empty

- `labs/workspaces/xmars_dojo/` exists and contains **no files**.
- The only dojo artifact anywhere is `labs/scratch/dojo_test/run_upgp_crash_test.py`. No scanner or Byzantine record lives in a dojo.

### 2.2 UPGP has real adversarial artifacts

- `tests/exploits/`: `exploit_ptrace.c`, `exploit_proc_mem.c`, `exploit_unshare.c`, `exploit_bpf.c`, `exploit_raw_socket.c` plus compiled binaries and `build_exploits.sh`.
- `tests/RedTeamExploitGauntlet.ts` drives them.
- So `docs/audits/UPGP_V3_BYZANTINE_FULL_PRESSURE_TEST_AUDIT.md` has a genuine target set behind it. That one is not theater.

### 2.3 The "Byzantine swarm" engines are plurality counters

`core/ops/scripts/max_byzantine_swarm.zig` (real arm64 binary, run today):

```
Honest Nodes: 666545 | Byzantine: 333455
Network Agreement: 66.65% | Final Approved State: 12444.89
[VERDICT] 0xBEAF. Swarm Integrity Maintained.
```

The algorithm is one pass over 1,000,000 tags, bucketed by bit pattern, taking the modal value. There are no rounds, no signed proposals, no view change, no `3f+1` membership — the things that make PBFT PBFT. The file header calls it a **"MAXIMUM BYZANTINE FAULT TOLERANT (PBFT) SWARM ENGINE"**. That is false labeling. It is a fault-tolerance *vote simulation*, and a useful one, but it is not consensus.

Same for `swarm_ramp.zig`, whose numbers we gave the reviewer yesterday. Calling those rows "Byzantine consensus" was an overstatement on our part; they are adversarial plurality counts. The 50.1% flip is a property of majority rule, not evidence of a BFT protocol.

`byzantine_corruption_sweep.zig` has valid source but its checked-in binary `core/ops/scripts/byzantine_corruption_sweep` is **0 bytes** — the same phantom-artifact class as the zero-size Ollama tags.

### 2.4 Audits that overstate their artifact

| Document | Claim | What the artifact does |
|---|---|---|
| `BYZANTINE_BREAKING_POINT_RAMP_AUDIT.md` | Liar density 10%→95% all `AIRTIGHT_QUARANTINED`; breaking point `100.0` | `byzantine_breaking_point_ramp.py` calls `governor.evaluate_write_candidate()` with `source_path="non_existent.json"` and `merkle_hash="badhash"`. Every stage is rejected for the same provenance reason regardless of "liar density". The table measures *bad hash rejection*, not resilience to liars. |
| `XORAS_015_SWARM_CONSENSUS_LAYER4_VERIFICATION.md` | Z3 `unsat` for Trinity 2-of-3 and 16,000-node latency ≤ 70 ms | No trinity `.smt2` exists in the tree (`find *.smt2` yields MTPO/UPGP/cage only). The real artifact is `core/ops/scripts/trinity_gate.py`, a 2-of-3 **file-hash** gate. Z3 was not involved. |
| `EXTREME_BYZANTINE_MAXOUT_TELEMETRY.json` | Name implies Byzantine consensus results | Pillars are `vector_engine`, `poincare_manifold`, `hexcell_memory`, `streaming_entropy`, `mast_taxonomy`, `atomic_mutex`, `http_stage_saturation`, `pyramidal_distillation`. **No consensus pillar.** Throughput bench under a misleading name. |
| `SWARM_BYZANTINE_CODEBASE_AUDIT_REPORT.md` | "100% Verified" | A repository inventory/health scan. Not a Byzantine test. |
| `ELITE_BYZANTINE_100K_REPORT.md` | 100,000-node swarm | States plainly it is a local `asyncio` simulation. **Honest** — no correction needed. |

### 2.5 What real quorum code we do have

- `core/ops/scripts/trinity_gate.py` — 2-of-3 distinct-agent approval, verifies SHA-256 of audio briefings on disk, fails closed below 2 votes. Real, file-based, not networked BFT.
- `core/ops/scripts/local_quorum_deliberation.py` — 3 local LLM seats via Ollama. Deliberation, not agreement cryptography.
- `core/ops/security/*.smt2` — MTPO pre-order, AGM monotonicity, UPGP containment, DART cage. These are real Z3 proofs and `reality_gate.sh` discharges them (`UNSAT`).

---

## 3. What this changes

1. **The gate is not the ceiling if it is wired in-process.** Rust at 14.36 µs would move the single-core scan ceiling from ~5,100/s to ~69,600/s. Through FFI or a daemon, 512 workers stop queueing on the scanner. Through a subprocess, it gets 12× worse. Wiring is the whole decision.
2. **Rename or correct the misleading artifacts** before any reviewer finds them: `xoras_ast_parser` (not an AST parser), `crypto_swarm` (not a swarm), `max_byzantine_swarm` header ("PBFT"), `EXTREME_BYZANTINE_MAXOUT_TELEMETRY` (no consensus data), `BYZANTINE_BREAKING_POINT_RAMP_AUDIT` (density not varied), `XORAS_015` (Z3 claim without an SMT file).
3. **Quarantine the 0-byte `byzantine_corruption_sweep` binary** with a receipt; don't delete.
4. **Say "plurality vote simulation"** wherever we currently say "Byzantine consensus", including the Grok thread. Real BFT needs signed proposals, view change, and `3f+1` membership. We have the 2-of-3 file gate and Z3 containment proofs; we do not have networked BFT.

## 4. Limits of this review

- Parity is 26 payloads from our own gauntlets, not an independent corpus.
- The Rust engine was measured in-process only; no FFI/PyO3 bridge exists, so the 14.36 µs figure is not yet reachable from Python.
- One host, one compiler version (`rustc 1.95.0`), no cross-host witness.
