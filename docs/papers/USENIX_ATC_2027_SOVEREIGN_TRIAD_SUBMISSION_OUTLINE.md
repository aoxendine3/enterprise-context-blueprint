# USENIX ATC '27 Submission Outline & Research Manuscript Spec

**Paper Title:** Monotonic Trajectory Pre-Order Concurrency and Mechanical Recovery for Autonomous Multi-Agent Swarms  
**Short Title:** The Sovereign Triad (MTPO, MARS & REASONS)  
**Authors:** The Lead 9 Council (DAXX, Vance, Clara, Max, Orion, Celine, John, Jarvis, Maxx)  
**Affiliation:** XORAS Systems / Sovereign Research Group  
**Target Venue:** USENIX Annual Technical Conference (USENIX ATC '27)  
**Track:** Operating Systems, Distributed Systems, and Autonomous Runtimes  
**Status:** Pre-Submission Research Draft & Formal Specification  

---

## Abstract

As large language model (LLM) agents transition from single-turn chat interfaces to autonomous multi-agent operating swarms, classical concurrency control protocols fail. Traditional Two-Phase Locking (2PL) induces multi-minute deadlocks during token generation, while Optimistic Concurrency Control (OCC) aborts conflicting transactions, discarding expensive inference compute and triggering cascading retry storms. Recent academic proposals (e.g., CoAgent) introduce static pre-orders but rely on the LLM itself as the runtime repair mechanism, trading transaction aborts for unbounded inference latency, token bloat, and stochastic non-convergence.

We present **MTPO (Monotonic Trajectory Pre-Order)**, a concurrency design for multi-agent swarms that couples monotonic serialization ranks ($\sigma$) with a three-phase Saga protocol in which every speculative mutation pre-registers an algebraic inverse ($\Delta^{-1}$). We give a Z3 (QF_ALIA) encoding in which trajectory monotonicity, defined as prefix-immutability of an append-only log, is *derived* from the semantics of saga operations rather than assumed: the MTPO model is `unsat`, a companion model of destructive AGM contraction is `sat` with a concrete witness, and a mutant that overwrites history flips back to `sat`. The result holds for the abstract log model only. We also report a typed-link storage layout whose SQLite WAL growth is $2.3\times$–$16\times$ smaller than a monolithic-JSON baseline over 100–1,000 commits (range across macOS arm64 and Linux x86_64), a ratio that grows with log length because the baseline rewrites a growing document and varies by platform. We do not yet report a live LLM-in-the-loop comparison, sustained fault injection, or multi-writer contention results; these are stated as future work. Mechanical recovery applies only where a deterministic inverse or compiler invariant is pre-declared.

---

## 1. Introduction

* **The Problem:** Multi-agent autonomous software systems require shared memory and collaborative mutation of codebases, databases, and configuration artifacts.
* **The Classical Failure:**
  * 2PL blocks worker threads for the full duration of inference calls (e.g. 10–120 seconds), causing system-wide latency collapse.
  * OCC aborts and retries on write-after-read conflicts, exponentially wasting token budgets and driving agent execution into live-lock loops.
* **The CoAgent Paradox:** CoAgent (SJTU, 2026) eliminates transaction aborts by establishing a total agent rank order and delivering one-way advisory notifications. However, CoAgent delegates error recovery to the LLM. In practice, prompt-based self-healing exhibits stochastic failure, hallucination drift, and massive token costs.
* **The Sovereign Triad Contribution:**
  1. **Derived Monotonicity Result:** A Z3 encoding in which prefix-immutability follows from the semantics of saga operations, with a satisfiable counter-model for destructive contraction and a mutation check showing the proof is not vacuous (abstract log model only).
  2. **Inverse-Registration Discipline:** Pre-registering an algebraic inverse ($\Delta^{-1}$) before each speculative mutation, so that undo for *reversible* operations is mechanical. Recovery cost and convergence against LLM self-patching are not yet measured.
  3. **Typed-Link Storage Layout:** A typed-edge layout in `world_file.db` whose WAL growth is lower than a monolithic-JSON baseline (measured curve, §5.2). The layout does not remove SQLite's single-writer limit.
  4. **Reproducible Verification Artifacts:** A fail-closed clean-room suite (expected solver results pre-declared, mutation check, property tests) executed in CI on Linux x86_64 and macOS arm64.

---

## 2. Background and Related Work

### 2.1 Concurrency Control in Multi-Agent Systems
* Review of 2PL, MVCC, and OCC under long-running inference transactions.
* The CoAgent protocol (Lyu et al., SJTU 2026): Serialization ranks $\sigma$, speculative reads, ToolSmith footprint extraction.
* Comparison of the *Locus of Intelligence*: LLM-driven prompt patching vs. bare-metal runtime invariants.

### 2.2 Formal Epistemology & Belief Revision
* Alchourrón–Gärdenfors–Makinson (AGM) Postulates (1985): Expansion ($+$), Contraction ($\div$), Revision ($*$), and Levi Identity.
* Epistemic entrenchment and the risk of non-monotonic causal inversion in distributed agent histories.

### 2.3 Structured Prompt-Driven Development (SPDD)
* Zhang & Xia (Thoughtworks 2026) / Martin Fowler: The REASONS Canvas (Requirements, Entities, Approach, Structure, Operations, Norms, Safeguards).
* Evolution from developer IDE prompt discipline to machine-checked autonomous agent execution contracts.

---

## 3. Formal Architecture & The Monotonicity Invariant

### 3.1 Mathematical Formulation of Monotonic Serialization Ranks
* Let swarm $\mathcal{S} = \{A_1, A_2, \dots, A_N\}$ with ranks $\sigma: \mathcal{S} \to \mathbb{N}^+$.
* State trajectory $\tau = [s_0, s_1, \dots, s_t]$ in shared state space $\Omega$.
* Trajectory monotonicity condition:
  $$\forall e_i, e_j \in \mathcal{E}, \quad e_i \prec_{\tau} e_j \implies \text{seq}(e_i) \le \text{seq}(e_j)$$

### 3.2 Monotonicity as a Derived Property
* **Model.** A trajectory is a log $H:\mathbb{Z}\to\mathbb{Z}$ with length $n$. Expansion is $H' = H[n \mapsto d]$. Saga contraction of entry $k<n$ is $H' = H[n \mapsto -H[k]]$ (append the inverse; never overwrite). Monotonicity means $n' \ge n \wedge \forall i<n.\ H'[i]=H[i]$.
* **Theorem 1 (saga operations are monotone).** The negation of monotonicity under expansion or saga contraction is `unsat` in QF_ALIA (`agm_mtpo_monotonicity.smt2`). It follows from the array read-over-write axiom, not from an assumption that MTPO is monotone. (An earlier encoding assumed this as an axiom and was circular; it is withdrawn.)
* **Theorem 2 (destructive contraction is not monotone).** With contraction defined as $H' = H[k \mapsto 0]$, the same negation is `sat` (`agm_unconstrained_violation.smt2`, witness $n{=}1,k{=}0$).
* **Non-vacuity check.** Changing saga contraction to overwrite entry $k$ makes the MTPO file `sat`; the suite verifies this on every run.
* **Scope.** This is a statement about an abstract append-only log. It does not by itself establish that a concrete implementation, with concurrent agents, ranks, and crashes, is monotone. Modeling rank-ordered concurrent writers is open work.

---

## 4. System Implementation & Memory Geometry

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   XORAS CONTROL PLANE & TENSOR PLANE SPLIT                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ CONTROL PLANE: Z3 SMT2 Monotonicity Proofs + Clara Merkle-DAG Provenance    │
├─────────────────────────────────────────────────────────────────────────────┤
│ TENSOR PLANE: UDP 11434 / 3,200-Byte HexCell SIMD Lattice (14.8M ops/sec)   │
├─────────────────────────────────────────────────────────────────────────────┤
│ PERSISTENT TIER: `world_file.db` 56-Byte Typed Links + Delta Reconciliation │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.1 Dual-Plane Separation
* **Control Plane (0.01% throughput):** Formal Z3 SMT2 invariant gates, Ed25519 payload signing, Merkle leaf commitment.
* **Tensor Plane (99.99% throughput):** Lock-free, zero-copy POSIX shared memory ring (`xoras_shm_ring.zig`) aligned to Apple Silicon M4 128-byte cache lines.

### 4.2 Typed-Link Storage Layout
* Edge typing in the style of property-graph models, with delta-style updates rather than whole-document rewrites.
* Logical schema: one row per edge in `typed_links` (`source_id`, `target_id`, `link_type`, `rank`, `timestamp`, `signature`).
* Measured WAL behaviour is given in §5.2 as a curve; no single reduction factor is claimed.

### 4.3 Clara Bidirectional Artifact Provenance Engine
* Merkle-DAG lineage tracking for every code, configuration, and audit artifact.
* Explicit tracking of `supersedes_hash` and `superseded_by_hash`, providing instant bidirectional traversal across historical revisions.

---

## 5. Evaluation

### 5.1 Verification Results (measured)
All results below come from `dist/sovereign_falsification_suite/run_falsification.py` (v2), which exits non-zero if any pre-declared expectation fails. Executed locally (macOS arm64) and in CI (Linux x86_64, macOS arm64 GitHub runners).

| Check | Pre-declared expectation | Observed |
| :--- | :--- | :--- |
| MTPO log model (`agm_mtpo_monotonicity.smt2`) | `unsat` | `unsat` |
| Destructive AGM contraction (`agm_unconstrained_violation.smt2`) | `sat` | `sat`, witness $n{=}1, k{=}0$ |
| Mutant: saga contraction overwrites history | `sat` (proof must not be vacuous) | `sat` |
| Saga implementation, 5,000 random logs | prefix preserved and effect undone | 5,000 / 5,000 |
| Mutant implementation, same 5,000 logs | must be detected | 251 / 5,000 pass (detected) |

*The verification suite and Lean 4 kernel check executed in CI on Linux x86_64 (Azure) and macOS-14 arm64 GitHub runners: run [38708977957](https://github.com/aoxendine3/enterprise-context-blueprint/actions/runs/38708977957). Both runners compiled the pinned Lean 4 toolchain (v4.35.0), verified that `step_monotone` and `reaches_monotone` hold without `sorryAx`, verified non-monotonicity of destructive contraction and mutants, and verified 1:1 differential agreement with Z3 SMT2 outputs.*

### 5.2 Storage: WAL Growth Curve (measured)
SQLite WAL, autocheckpoint disabled, one commit per mutation. Baseline: a single JSON document rewritten on each mutation. Typed: one row per edge.

| Commits | Monolithic JSON | Typed links | Ratio (macOS arm64) | Ratio (Linux x86_64, CI) |
| ---: | ---: | ---: | ---: | ---: |
| 100 | 954 KB | 414 KB | 2.3× | 2.3× |
| 500 | 13.9 MB | 2.3 MB | 6.0× | 8.8× |
| 1,000 | 47.0 MB | 4.9 MB | 9.6× | 16.0× |

Byte columns are from the macOS arm64 run. The ratio varies with log length and with platform, so no single reduction factor is claimed; we attribute the platform difference to filesystem and page-handling behaviour but have not isolated the cause.

The ratio is not a constant: the baseline is quadratic in log length because it rewrites a growing document. A fixed figure from one run (an earlier draft's "3.88×") depended on checkpoint timing and is withdrawn. Typed links cost roughly 4–5 KB of WAL per commit, since SQLite logs whole pages, so a "56-byte edge" describes the logical row, not WAL cost. A fairer baseline (one row per edge in a conventional relational schema) is future work and would be expected to narrow the gap substantially.

### 5.3 Limitations of This Evaluation
* **No live LLM baseline.** An earlier draft's LLM figures (tokens, latency, 95% convergence) came from a parameterized simulation, not measurements. They are removed. Comparing mechanical recovery with LLM self-patching requires live API runs and is future work.
* **Mechanical recovery latency is not reported as a headline.** Earlier sub-0.1 ms figures timed a trivial in-process operation (a `compile()` call on a fixed string), not recovery of a real fault, and the "100% convergence" figure was constant in the harness rather than measured.
* **Abstract model.** The Z3 result covers the log model in the `.smt2` files. It does not cover integer overflow of ranks, memory reordering, crashes during `fsync`, or non-invertible side effects.
* **Single-writer storage.** Typed links reduce WAL volume; they do not change SQLite's single-writer limit. Multi-writer contention is unmeasured.
* **Scaling figures.** The 100,000-agent and 14.8M ops/sec figures come from separate internal benchmarks that are not part of the public falsification suite and have not been externally reproduced.

---

## 6. Discussion, Limitations & Governance
* **Reversibility Domain:** Mechanical Saga inverses are strictly bounded to operations with pre-registered algebraic inverse functions ($\Delta^{-1}$) or deterministic compiler AST rules. For non-invertible external side effects (e.g., third-party HTTP payments, external webhook emissions, physical actuation), mechanical rollback cannot apply; runtime advisory notifications and cognitive compensatory re-planning remain strictly necessary.
* **Axiomatic SMT2 Limits:** The Z3 SMT2 trajectory monotonicity proof verifies the declared QF_LIA state-transition axioms. It does not model bare-metal kernel failures, power loss during fsync, or weakly-ordered hardware memory bus reordering.
* **The Human Protection First Invariant:** In compliance with Sovereign Log Entry #078, mechanical fail-closed gates protect human safety and clinical integrity above operational throughput.
* **Open-Source Availability & External Falsification:** Complete clean-room falsification suite, Lean 4 proofs, and GitHub Actions matrix runs are publicly available at `https://github.com/aoxendine3/enterprise-context-blueprint/actions/runs/38708977957` (fail-closed suite with Lean 4 kernel verification).

---

## 7. Conclusion

Within a defined domain (reversible mutations with pre-registered inverses), we showed in an abstract log model that saga-style contraction preserves trajectory monotonicity while destructive contraction does not, and we measured the storage cost of a typed-link layout against a monolithic baseline. Whether this yields lower recovery cost or higher convergence than LLM-in-the-loop repair on real workloads, and whether the property survives concurrent writers and crashes, remains to be measured.
