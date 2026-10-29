# XORAS SOVEREIGN UNIFIED CANONICAL SPECIFICATION & EVIDENCE BASE
### Document ID: `XORAS-CANONICAL-SSOT-2026`
### Status: FROZEN & UNIFIED SSOT | Canonical Source for MTPO, MARS, REASONS, GitHub Pages & Repos

---

## 1. Executive Grounding & Core Mission
**XORAS** is an enterprise-grade sovereign multi-agent execution framework created by **Anthony Junior Oxendine** ([@AnthonyOxe93342](https://x.com/AnthonyOxe93342)).

All claims, architecture documentation, website pages, and repository specifications across **MTPO**, **MARS**, and **REASONS** derive from this single authoritative canon:
- **PyPI Release:** [`xoras-agent-framework`](https://pypi.org/project/xoras-agent-framework/) (v2.4.3)
- **Main Repository:** [`github.com/aoxendine3/xoras`](https://github.com/aoxendine3/xoras)
- **Hugging Face Hub:** [`huggingface.co/XORAS-CORE`](https://huggingface.co/XORAS-CORE)
- **Hugging Face Portal:** [`huggingface.co/spaces/XORAS-CORE/XORAS-SENTINEL`](https://huggingface.co/spaces/XORAS-CORE/XORAS-SENTINEL)
- **YouTube Channel:** [`youtube.com/@xorassystems`](https://www.youtube.com/@xorassystems/)

---

## 2. The Sovereign Triad: MTPO, MARS & REASONS

### 2.1 MTPO (Monotonic Trajectory Pre-Order)
- **Purpose:** Mathematical concurrency and state isolation engine for autonomous multi-agent systems.
- **The Core Mechanics:**
  1. **Judge-Gate (Single-Writer Principle):** Every shared memory key is assigned an exclusive Owner Agent. Collaborators propose deltas; only the designated owner commits.
  2. **Witness-Gate (Monotonic Compare-And-Set):** All writes enforce atomic CAS against monotonically increasing versions (`v_prior` $\rightarrow$ `v_new`). Stale writes fail closed.
  3. **Reversible Pre-Order:** Reversible trajectory transitions that preserve historical causal order forward in time without deleting prior history (preventing AGM postulate collapse).
- **Physical Hardware Performance:**
  - Tested on physical Apple Silicon M4 unified memory.
  - Multi-threaded atomic operations: **16 physical worker threads** operating across lock-free POSIX shared-memory ring buffers achieving **8.58M–10.2M operations/second**.
- **Empirical Receipt:** `memory/catch_log/TWO_AGENT_ZERO_LOST_UPDATES_RECEIPT.json` (**20 concurrent operations, exactly 0 lost updates**).

### 2.2 MARS (Multi-Agent Reasoning Structure & Defense Sandbox)
- **Purpose:** Eliminating the self-grading conflict of interest and enforcing fail-closed sandbox containment.
- **The Core Mechanics:**
  1. **Independent Blackbox Validation:** Verifying agents operate in an isolated subprocess with zero access to author reasoning or prompts. Evaluates solely on Abstract Syntax Tree (AST) structure, schema contracts, and subprocess execution exit codes (`code == 0`).
  2. **14-Gate Defense-in-Depth Sandbox:** Kernel-level process isolation using POSIX Discretionary Access Control (DAC), read-only mounts, capability dropping, and seccomp filters. (Replaces deprecated synthetic bitwise SMT proofs with verified kernel system boundaries).
  3. **Fail-Closed Gate Model:** Any divergence, unowned state mutation, or unauthorized syscall escape halts execution immediately and quarantines the candidate payload.
- **Empirical Receipt:** `memory/catch_log/INDEPENDENT_VALIDATOR_RECEIPT.json` (Blind acceptance test catching syntax defects, schema violations, and runtime crashes).

### 2.3 REASONS (The Enterprise Context & Lineage Engine)
- **Purpose:** Compiling unstructured human intent and multi-turn workflows into immutable, cryptographically verifiable context directed acyclic graphs (DAGs).
- **The Core Mechanics:**
  1. **7-Dimensional Context Canvas:** Intent, Boundaries, Constraints, Knowledge Lineage, Agent Assignment, State Transitions, and Verification Assertions.
  2. **Merkle Lineage & Epistemic Audit:** Every state mutation and tool execution is fingerprinted with an authoritative SHA-256 hash forming a continuous Merkle tree.
  3. **Cross-Lineage Quarantine (Anti-CLIA):** Blocks cross-session unlinked replay attacks by enforcing Merkle provenance verification before state admittance.
- **Empirical Receipt:** `memory/catch_log/TRI_WITNESS_CROSS_VALIDATION_RECEIPT.json`.

---

## 3. Physical Hardware & Storage Fabric (The 6 Tiers)
1. **TonyDB:** Native compiled Zig engine with 3,200-byte cache-aligned HexCells (32B header + 512B 128-D vector + 2656B payload) and POSIX WAL recovering in **3.34 ms**.
2. **POSIX Shared-Memory Ring Buffer:** `<0.04 µs` zero-copy IPC mapped directly into M4 unified RAM (`libshm_ring_buffer.dylib`).
3. **Attestation Service:** Native Zig HMAC-SHA256 notary on port 8081 backed by SurrealDB.
4. **DojoDB:** Adversarial test database logging multi-agent gauntlet receipts.
5. **LanceDB:** Columnar embedded vector storage for cold-tier spillover.
6. **SQLite WAL & Cloud Storage:** Local single-writer blackboards with S3/R2 protocol connectors for remote checkpoint snapshots.

---

## 4. Unified Mathematical Invariant
$$\mathcal{D}_{\text{lattice}} = 24 \text{ Poincaré Heads} \times 768 \text{ Dimensions} = \mathbf{18,432\text{ Dimensions}}$$
Evaluated under the Poincaré Ball Model of hyperbolic geometry ($K = -1.0$) preserving graph hierarchies with minimal distortion.
