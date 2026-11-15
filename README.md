# Agent Notary by XORAS

**Proving what your agents actually did — cryptographically.**

Agent Notary is the sovereign, dual-implementation verifier for autonomous multi-agent systems. Every claim your agents make is recomputed independently before it is accepted. No claim advances on trust. No artifact advances without a verifiable, attributable proof — Ed25519-signed, Merkle-anchored, and discharged by a second, independent codebase.

| What Agent Notary verifies | How |
| --- | --- |
| Every agent action | Notarized via independent recomputation (Zig + Python dual-witness) |
| Every artifact | Merkle-attested, attribution pinned, unforgeable receipt |
| Every state transition | DAG lineage verified across 3,262+ nodes, zero drift |
| Every release | 6/6 production gates discharged — E2E, telemetry, Z3, Zig verifier, TypeScript gauntlet, 14-gate BBQ, Rust crates |
| Every shipped artifact | WORM-attested and independently verifiable offline |

**Website:** https://aoxendine3.github.io/xoras.infotech/  &nbsp;·&nbsp; **Product brief:** https://aoxendine3.github.io/xoras.infotech/product.html

---

## How to read this repo (for critics and engineers)

There are **three surfaces** and they tell one story:

| Surface | What it is | Status |
| --- | --- | --- |
| **Agent Notary (site)** — <https://aoxendine3.github.io/xoras.infotech/> | The front door. What you buy or evaluate. | Live. Landing page, product brief, security model, download. |
| **This repository (enterprise-context-blueprint)** — the technical substrate | The engineering evidence: gates, receipts, witnesses, DART cage, MERKLE spine. | Active, verified evidence; engineering discipline 6/6 gates; still pre-1.0. |
| **UPGP Proving Ground** — <https://github.com/aoxendine3/upgp-proving-ground> | The research proving ground with falsification and measured side-channel receipts. | Research-track; not a shipped product. |

**The agent family:** every XORAS agent is one of three things: a **counselor** on the council (internal citizens on a sovereign loop), a **witness** (independent re-execution), or a **notary** (the product). All three speak the same evidence format: receipts in `memory/catch_log/`, Merkle spine in `memory/tri_brain/`.

**What to check (in 10 minutes, honestly):**
1. `bash ops/scripts/verify_all_production_gates.sh` — six gates, must print `6/6 PASSED` and exit 0 on a clean checkout.
2. `python3 tests/test_dart_cage_lattice.py` — cage lattice acceptance, 7/7.
3. `python3 scratch/golden_groundedness_harness.py` — groundedness evaluation vs the golden question set. No model on this host scores above the ship threshold yet — that is a fact, not a flourish.
4. `cat memory/catch_log/REALITY_GATE_RECEIPT.json` — the most recent pre-flight receipt.
5. Read `AGENTS.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`.

**What we do not claim (yet):** that any benchmark is independently replicated at an organization's scale, that our gates are publicly audited, or that the product has served a paying customer. Everything we publish is either a receipt or a roadmap item labeled as such.

---

---

> Hallucination/context-grounding material is tracked with provenance in `docs/papers/` — nothing there is presented as verified unless receipted in `memory/catch_log/`.

# Enterprise Context Blueprint: The Sovereign Triad (MTPO, MARS & REASONS)

[![Outside CI Gauntlet](https://img.shields.io/badge/Outside_CI-Run_%2338708977957_(Ubuntu_24.04_%2B_macOS--14)-10b981.svg)](https://github.com/aoxendine3/enterprise-context-blueprint/actions/runs/38708977957)
[![UPGP v5.0 Ultra](https://img.shields.io/badge/UPGP-v5.0_Ultra-00f2fe.svg)](https://aoxendine3.github.io/upgp-proving-ground/)
[![Lean 4 Verified](https://img.shields.io/badge/Lean_4-0_sorryAx_(v4.35.0)-8b5cf6.svg)](dist/sovereign_falsification_suite/lean/MtpoMonotonicity/Basic.lean)
[![Z3 Differential](https://img.shields.io/badge/Z3_SMT2-Differential_UNSAT-38bdf8.svg)](dist/sovereign_falsification_suite/agm_mtpo_monotonicity.smt2)
[![Target Venue](https://img.shields.io/badge/Target_Venue-USENIX_SAIS_'27-f59e0b.svg)](docs/papers/USENIX_SAIS_2027_SOVEREIGN_TRIAD_FULL_PAPER.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **The Sovereign Triad** is the formal, evidence-governed operating runtime for autonomous multi-agent systems, integrating **UPGP v5.0 Ultra** containment research, MTPO concurrency checked by Z3, and an anti-context-failure discipline under active development. Results are reported as measured, not asserted.

---

### Monotonic Trajectory Pre-Order (MTPO): The Mathematical Concurrency Paradigm

**Monotonic Trajectory Pre-Order (MTPO)** is the exact, non-negotiable term and mathematical bedrock of our concurrency architecture in **XORAS::OS**. 

Classical database isolation models—specifically **Two-Phase Locking (2PL)** and **Optimistic Concurrency Control (OCC)**—break down catastrophically when applied to autonomous multi-agent workloads running long-horizon LLM inference loops:

* **2PL Failure**: Locking files or database records across multi-second or multi-minute agent reasoning cycles causes immediate CPU thread starvation, lock contention, and system-wide **lock deadlocks**.
* **OCC Failure**: OCC detects conflicts at commit time and aborts the entire transaction. In parallel agent swarms, aborting a transaction throws away minutes of high-cost GPU/NPU compute and burns token budgets without advancing system state.

```text
               MONOTONIC TRAJECTORY PRE-ORDER (MTPO) CONCURRENCY FLOW
               
  [ CONCURRENT AGENTS ] ──► Assigned Monotonic Serialization Ranks (σ_1 < σ_2 < σ_3)
           │
           ▼
  [ ORDER-FILTERED READS ] ──► Reads contain ONLY committed writes of rank ≤ σ
           │
           ▼ (Out-of-Order Speculative Write Occurs)
  [ THREE-PHASE SAGA INVERSE ] ──► Prepare ──► Execute ──► Reverse (Rolls back diff)
           │
           ▼
  [ ADVISORY SIGNAL QUEUE ] ──► Pushes ν_i→j signal to Higher-Rank Reader
           │
           ▼
  [ IN-SITU SELF-HEALING ] ──► Higher-Rank Agent updates plan without thread halt
```

---

### Core Mechanics of MTPO

1. **Monotonic Serialization Ranks ($\sigma$)**: Every agent citizen on the roster is assigned a fixed, monotonic serialization rank ($\sigma_1 < \sigma_2 < \sigma_3$) at session launch. This rank establishes a definitive logical timeline that remains completely independent of physical arrival time.
2. **Order-Filtered Snapshot Reads**: When agent $A_j$ reads an object, the middleware serves a virtual snapshot containing only writes committed by agents with an equal or lower rank ($\le \sigma(A_j)$), screening out speculative changes from higher-rank workers.
3. **Three-Phase Saga Inverses**: Every write registers a deterministic three-phase undo operation (*Prepare, Execute, Reverse*). If an out-of-order write arrives from a lower-rank authority, the runtime automatically executes the *Reverse* action (such as applying a localized git diff rollback), applies the lower-rank write, and re-applies the sequence chronologically.
4. **Non-Blocking Advisory Notifications ($\nu_{i \to j}$)**: When a lower-rank write invalidates a premise read by a higher-rank agent, the runtime pushes a non-blocking advisory signal ($\nu$) directly into the higher-rank agent's prompt context. The agent evaluates the notification and performs a surgical **in-situ self-healing repair** on its active plan without restarting the session or discarding compute.

---

---

### 4. Deep Architecture: The MARS Framework & The REASONS Canvas

In **Xoras Systems**, the **MARS Framework** (Multi-Agent Reasoning Structure) and the **REASONS Canvas** (from Structured-Prompt-Driven Development / SPDD) form the dual pillars of our deterministic execution plane. Together, they bridge the gap between high-level human intent and low-level physical silicon execution (`aarch64-apple-darwin`).

```text
       THE REASONS CANVAS ──► INTENT GRAPH ──► MARS VERIFICATION GATES

  ┌───────────────────────────────┐        ┌───────────────────────────────┐
  │      THE REASONS CANVAS       │        │   MARS FOUR-LAYER GATE        │
  │ R - Requirements & DoD        │        │ Layer 1: AST Syntax Linter    │
  │ E - Entities & Graph Schemas  │ ──►    │ Layer 2: Ed25519 SAST Security│
  │ A - Approach & Pattern        │        │ Layer 3: ASAN/TSAN Sandbox    │
  │ S - Structure & Dependencies  │        │ Layer 4: ≥ 80% Unit Test Pass │
  │ O - Concrete Method Steps     │        └───────────────────────────────┘
  │ N - Norms & Style Conventions │                       │
  │ S - Safeguards & Invariants   │                       ▼
  └───────────────────────────────┘             [ MERGE TO CORE REALITY ]
```

#### I. The REASONS Canvas: Compiling Intent to Graphs
Prompting an autonomous swarm in raw, unstructured natural language is the modern equivalent of writing machine code in raw assembly. Under **Structured-Prompt-Driven Development (SPDD)**, we reject conversational prompting in favor of the **REASONS Canvas**, which compiles goals into version-controlled engineering specs:

1. **Requirements (R)**: Explicit problem statement paired with a mathematically verifiable Definition of Done (DoD).
2. **Entities (E)**: Mapped domain objects, schemas, and relational context graphs.
3. **Approach (A)**: High-level architectural strategy, cleanly isolated from immediate tool calls.
4. **Structure (S)**: System dependencies, structural module bindings, and directory exclusions (e.g., locking `/barn/`).
5. **Operations (O)**: Decomposed, testable method signatures and linear step execution plans.
6. **Norms (N)**: Memory-safety standards, defensive typing, and byte-aligned I/O rules.
7. **Safeguards (S)**: Non-negotiable security boundaries, Ed25519 payload signatures, and single-use capability tokens.

The **Conductor** reads the compiled REASONS Canvas and converts it into a **Directed Acyclic Graph (DAG) Intent Graph**. If cyclic dependencies or ambiguous execution paths occur, execution halts immediately with an `EpistemicAnomalyException` before a single GPU token is wasted.

---

#### II. The MARS Framework: Observer-Critic & Four-Layer Verification
To eliminate the **self-grading conflict of interest**—where the agent generating the code evaluates its own work—the **MARS Framework** decouples execution from validation using an independent **Observer-Critic Swarm** and a non-negotiable **Four-Layer Mechanical Gate**:

* **Layer 1: AST Syntax & Linter Verification**: Automatic parsing, indentation, and structural syntax validation (`cargo fmt` / `clippy` / `pylint`).
* **Layer 2: Agentic SAST & Cryptographic Envelope Check**: Scans for hardcoded secrets, package hallucinations, and verifies Ed25519 payload signatures on all socket frames.
* **Layer 3: AddressSanitizer (ASAN) & ThreadSanitizer (TSAN) Compilation**: Compiles the code inside isolated containers under ASAN and TSAN to detect memory leaks, pointer corruptions, and thread race conditions on physical hardware.
* **Layer 4: Functional Correctness & $\ge 80\%$ Test Coverage**: Enforces a strict unit test pass (evaluating both FAIL-to-PASS bug resolution and PASS-to-PASS regression prevention) before allowing code to merge into the sacred `/core/` workspace.

---

### 5. Formal Verification & Outside Reproducibility

The entire mathematical formalization and empirical benchmark suite are packaged for one-command replication:

```bash
# Option A: One-command replication runner
./dist/sovereign_falsification_suite/reproduce.sh

# Option B: Isolated bit-identical Nix Flake
nix run github:aoxendine3/enterprise-context-blueprint#falsification-suite
```

* **Lean 4 Proofs**: `dist/sovereign_falsification_suite/lean/MtpoMonotonicity/Basic.lean` (`step_monotone` & `reaches_monotone` proved with `0 sorryAx`).
* **Z3 SMT2 Differential**: `dist/sovereign_falsification_suite/agm_mtpo_monotonicity.smt2` (`unsat` vs destructive contraction `sat`).
* **Outside CI Matrix**: [GitHub Actions Run #38708977957](https://github.com/aoxendine3/enterprise-context-blueprint/actions/runs/38708977957) verified across independent Azure Linux (x86_64) and Apple Silicon macOS-14 (arm64) runners.
* **Scientific Manuscript**: [`docs/papers/USENIX_SAIS_2027_SOVEREIGN_TRIAD_FULL_PAPER.md`](docs/papers/USENIX_SAIS_2027_SOVEREIGN_TRIAD_FULL_PAPER.md) (Targeted at USENIX SAIS '27).

---

⚡ **The REASONS Canvas locks intent; the MARS gates verify reality.**  
⚡ **Every claim in this repo is on the road to being machine-verified, or it is labeled as planned.**
