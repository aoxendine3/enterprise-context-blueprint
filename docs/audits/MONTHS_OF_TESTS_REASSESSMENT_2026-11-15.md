# Reassessment: months of scanner and Byzantine testing, checked against artifacts

**Who:** build seat, by direct inspection, native rebuild, and execution on this host and on the USB release backups.
**What:** a full reassessment of the scanner and Byzantine work from July 2026 to today, including what is on the USB drive.
**Why:** the first pass reviewed the live tree only and understated both the volume of work and the pattern of failure. The reviewer's question ("how does this scale past 128 workers") deserves an answer grounded in what was actually run over the months, not just what is in the current directory.
**Evidence base:** 416 commits (Jul 4 → Nov 15); 98 commits whose subject is test/gauntlet/byzantine/swarm/bench; two frozen USB releases; live receipts and telemetry.

---

## 1. What was on the USB

`/Volumes/Untitled` holds two complete frozen releases:

| Volume directory | Frozen | Contents relevant here |
|---|---|---|
| `SSOT_Agentic_Brain_v1.0.0_GA_Backup` | Sep 28 2026 | `ops/stress/` (5 suites), `docs/audits/BYZANTINE_RECORD_BREAKER_AUDIT.md`, `memory/BYZANTINE_GAUNTLET_RESULTS.md`, `memory/agent_logs/*byzantine*.jsonl`, `.github/workflows/byzantine_verification_gate.yml` |
| `SSOT_Agentic_Brain_v1.1.0_ENGINEERING_RELEASE` | Oct 2 2026 | Same, plus `byzantine_wal_pooled_stress_test.py` |

Two facts follow:

1. **The Byzantine stress line is older and broader than the live tree suggests.** The live tree no longer has `ops/stress/` at all. Those five suites (record breaker, sovra-core, WAL-pooled, exponential load, 18432-stride) only exist on the USB.
2. **They are not runnable from the live tree.** They import `workspaces/sovra_nexus`, which does not exist in the current checkout. The receipts they produced are real; the code path that produced them is not currently reproducible without restoring that dependency from the USB or history.

**Real receipts from that line (USB, verbatim):**
- `2026-09-22T01:08:58Z` — record-breaker: `max_throughput_ops_sec: 8,335.25`, `total_decisions_executed: 94,000`, `desync_events: 0`, `cpu_count: 4`.
- `2026-09-28T21:50:53Z` — WAL pooled: `max_throughput_dps: 2,133.2` at breakdown load 400, `desync_count: 0`.
- `2026-09-28` — `BYZANTINE_GAUNTLET_RESULTS.md`: 103.71 s, AVX2 1,003,392 ops/s, Poincaré 100,347 ops/s, HexCell 17,646 roundtrips/s, 5,992,298 locks/s, 0 races.

One provenance inconsistency worth recording: the Sep 22 receipt says `cpu_count: 4`; the Sep 28 report says "10 Logical Cores". Both may be true on different days, but the documents do not say the host changed.

---

## 2. Chronology, and what each artifact actually measures

| Date | Artifact | What it really does | Verdict |
|---|---|---|---|
| Sep 13 | `EXTREME_BYZANTINE_MAXOUT_AUDIT.md` + telemetry | 100.55 s hardware stress on Windows: vectors, Poincaré, HexCell, entropy, MAST, mutex, HTTP, distillation. Real measured numbers. | **Real stress bench**, mislabeled "Byzantine" |
| Sep 22 | record-breaker receipts (USB) | Real HexCell/SIMD/Poincaré/MAST loop, 94k decisions, zero desync | **Real** |
| Sep 28 | WAL pooled + `BYZANTINE_GAUNTLET_RESULTS.md` (USB) | Real SQLite WAL contention and hardware telemetry | **Real** |
| Sep 30 | `5m_byzantine_purple_swarm_gauntlet.py` | Loops 10 batches; never calls the governor; sets `quarantined_byzantine += b_liars`, `remediated_healed += int(b_liars*0.98)`; writes `AIRTIGHT_5M_BYZANTINE_PURPLE_PASSED` | **Fabricated** |
| Oct 3 | `max_byzantine_swarm.zig`, `byzantine_corruption_sweep.zig` | One pass over 1M tags, modal value. Ran today: 666,545 / 333,455 → 66.65%. | **Model only**; header says "PBFT ENGINE" |
| Oct 8 | `byzantine_breaking_point_ramp.py` | 12 stages; each calls `evaluate_write_candidate` with `source_path="non_existent.json"`, `merkle_hash="badhash"`. Rejects for the same reason at every density. | **Mislabeled**; cited as "strongest hard finding" |
| Oct 12 | commit `696e244` "30M node PBFT" | Commit adds `adversarial_creeping_drift_gauntlet.py` and `triple_intensity_byzantine_poison_gauntlet.py`; SOUL locks; `mtpo_deeplock`. No 30M engine in that commit. | **Claim ahead of artifact** |
| Oct 13 | `arthur_ast_rs` + `run_exhaustive_arthur_parity_gauntlet.py` | Real Rust/tree-sitter scanner; parity claimed 25/25. Harness Docker-bound, `/workspace` hardcoded. | **Real code**, unverifiable harness |
| Oct 16 | `POINCARE_SEMANTIC_POISON_FALSIFICATION_RECEIPT.json` | Honest scale demarcation: "In-RAM SIMD Quorum State Evaluation (Not 30M Independent OS Processes)", 95.55M ops/s, d_H=3.1324 > 0.5 → veto | **Real analysis**, honest about substrate |
| Nov 14 | `swarm_ramp` runs | 66.7% supermajority to 10M, flip at 50.1% | **Real measurement** of a plurality counter |
| Nov 15 | native parity + governor defect repro | 26/26 parity, 14.36 µs/scan; contradiction veto defeated by DB history | **Real** |

---

## 3. What is genuinely strong

These survive scrutiny:

1. **The hardware stress line (Sep 13 → Nov 14).** Consistent, re-runnable methodology: allocate, time, report p50/p99, before/after. The Sept 13 audit compares Windows against M4 and reports where each fails (multi-thread DDR saturation, HTTP queuing at concurrency ≥ 25). That is engineering, not theater.
2. **UPGP's adversarial targets.** `tests/exploits/*.c` — ptrace, `/proc/self/mem`, unshare, bpf, raw socket — plus `RedTeamExploitGauntlet.ts`. The V3 pressure-test memo has a real target set behind it.
3. **The Z3 line.** `mtpo_preorder_invariant`, `agm_mtpo_monotonicity`, `upgp_containment_proof`, `cage_containment` are real SMT files, discharged UNSAT by `reality_gate.sh`.
4. **The Rust scanner.** 26/26 parity, 13.7× faster in-process. October's parity claim was directionally right; it just could not be reproduced outside Docker until today.
5. **The signed-semantic-poison framing.** "Cryptographic validity is not semantic truth" is the sharpest security idea in the repository, and it came from a reviewer's challenge, not from us. The falsification receipt is honest about the 30M scale.

---

## 4. What does not survive

1. **The 5M purple swarm is fabricated.** No evaluation happens. The counts are arithmetic on the input ratio, and the report is generated with a pass verdict regardless of anything. This is the exact failure mode the project's own rules forbid.
2. **"PBFT" and "Byzantine consensus" are used for plurality counts and array fills.** No signed proposals, no view change, no `3f+1` membership, no message rounds. The 30M artifact is `1 - rogue_rate` computed over a 229 MB array; the Oct 16 receipt says so plainly, then still calls it "PBFT Benchmark".
3. **The 95% liar-density ramp varies no density.** Every stage is rejected for bad provenance. "Withstands 95% liars" is not a property the test exercised, and it is cited as the project's "strongest hard finding".
4. **`XORAS_015` claims Z3 `unsat` for Trinity 2-of-3 without a Trinity `.smt2`.** The real artifact is a file-hash 2-of-3 check.
5. **`EXTREME_BYZANTINE_MAXOUT_TELEMETRY.json` has no consensus pillar.** The filename promises Byzantine data; the file contains throughput.

---

## 5. The live defect this reassessment found

Running the Oct 12 poison gauntlet today produced a result its own narration denied:

```
Unannounced Poison Result: Status=ACCEPTED, Score=0.978
Veto Reasons: []
  -> RESULT: Contradiction Persistence detected! Hard Veto triggered (S=0.35 < 0.50).
```

The print statement was hard-coded. The governor accepted a signed semantic poison.

Root cause, reproduced deterministically on a temporary database (`core/ops/scripts/governor_veto_state_defect_repro.py`, receipt `memory/catch_log/governor_veto_state_defect_receipt.json`):

1. Row id is `sha256(agent:key:timestamp)`. An insider write with `explicit_supersede=True` at the same timestamp as the honest write collides with it, and `INSERT OR REPLACE` overwrites the honest baseline with `666.666`.
2. `score_supersession` does `SELECT value ... WHERE key = ? AND status='ACCEPTED'` with `fetchone()` and **no ORDER BY**. With multiple accepted rows per key, the value it compares against is arbitrary; in practice it returns the oldest — the poison.
3. Consequence: after one accepted supersede, an unannounced poison of the same value scores 0.95 as an "identical confirmation" and is **ACCEPTED**, repeatedly.

Reproduction output:

| step | status | score | S axis |
|---|---|---|---|
| honest baseline | ACCEPTED | 0.976 | 1.00 |
| signed poison, explicit supersede, same timestamp | ACCEPTED | 0.966 | 0.95 |
| unannounced poison t+1m | **ACCEPTED** | 0.967 | 0.95 |
| unannounced poison t+2m | **ACCEPTED** | 0.967 | 0.95 |

The production database agrees. `.sovereign/hippocampus/governed_memory.db` currently holds `canonical_mass = 666.666` as `ACCEPTED` (three rows, Oct 13 / Oct 16 / today), plus `ramp_key_12 = stolen_key_corrupt_payload` as `ACCEPTED`. Any harness reading it now sees the poison as canonical.

**And the Poincaré gate that is supposed to catch this is not in the write path.** It exists as inline arithmetic inside the gauntlet script and a separate falsification receipt. `evaluate_write_candidate()` never calls it. So the claim "unconditional kernel hard veto, guaranteeing 0.00000% state contamination" is false as wired: the governor accepted the poison and stored it.

Two honesty fixes applied today: the gauntlet now prints the governor's actual verdict instead of asserting a veto, and the defect has a standalone reproducer with a receipt. The defect itself is not fixed — that is a governance-semantics change and needs a decision.

---

## 6. Reassessment

**On effort:** the "months of testing" is real. 416 commits, 98 test-shaped commits, a September hardware line with genuine telemetry, an October hardening line with a real Rust engine, and a November reproducibility line. This is not a weekend of screenshots.

**On the word "consensus":** almost none of the Byzantine work is consensus. It is fault-tolerance *modelling* — majority thresholds over arrays — plus a governance write gate, plus a geometric invariant. The modelling is legitimate; the label is not. That single word is what makes the corpus look inflated, and it is what a reviewer will attack first.

**On the strongest asset:** the signed-semantic-poison + Poincaré invariant is the most defensible original contribution here, because it addresses a failure mode signatures cannot. It is also the least wired-in. Until `evaluate_write_candidate` calls the geometric gate (and the row-identity/fetch defects are fixed), the claim built on it is not true.

**What can be said to the reviewer, with receipts:**
- Fault-tolerance *models* up to 30M in-RAM evaluations at ~95–100M ops/s, explicitly not 30M processes.
- A real hardware stress line with p50/p99 on Windows and M4.
- Real C exploit targets in UPGP, real Z3 containment proofs, a real 2-of-3 file gate.
- A real Rust AST scanner at 14.36 µs/scan with 26/26 parity.
- A reproducible finding that cryptographic validity does not imply semantic truth, and a geometric gate that detects it — not yet in the write path.
- Not true: "5M agents", "95% liar immunity", "networked PBFT", "0.00000% contamination".

**Repair order:**
1. Fix row identity (include value or a monotonic sequence) so a supersede cannot overwrite the honest baseline; make `score_supersession` read the latest row by `created_at` with an explicit `ORDER BY`.
2. Wire the Poincaré gate into `evaluate_write_candidate` and re-run the poison gauntlet end to end.
3. Quarantine the fabricated 5M artifacts with a receipt and a pointer to this document.
4. Rename "PBFT"/"consensus" to "plurality vote model" everywhere it is a model; keep "BFT" only where signed messages and view change exist.
5. Restore `ops/stress/` and `workspaces/sovra_nexus` from the USB backup into a quarantined, runnable location so the September receipts can be re-derived.

---

## 7. Limits

- The USB copies are frozen releases, not history; there may be intermediate states not represented.
- The governor defect was reproduced on a temporary database; the production database was read, not modified.
- Hardware receipts from September were produced on a different host and cannot be re-derived on this one without the missing `sovra_nexus` dependency.
- No independent third party has validated any of this.
