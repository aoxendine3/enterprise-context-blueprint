# Technical Benchmark Report: Dual-Node Cross-Platform Architecture

**Document ID:** XORAS-TR-2026-014  
**Date:** October 20, 2026  
**Auditor:** XORAS Systems Technical Evaluation Group  
**Target Systems:**  
- **Node A (Control Plane):** Apple Silicon M4 (10-Core SoC, Unified LPDDR5X RAM, Darwin 24.x)  
- **Node B (Tensor Plane):** x86_64 Bare Metal (Windows 11 Pro, Host: `desktop-8p1gp53.lan`, LAN IP: `192.168.1.211:11434`)  
**Data Artifact:** `docs/WINDOWS_VS_M4_CROSS_NODE_CEILING_BENCHMARK.json`  

---

## 1. Executive Summary & Objective

This report provides an empirical evaluation of the XORAS Systems dual-node architectural design. The design separates deterministic control logic from probabilistic model execution across two dedicated physical machines:

1. **Control Plane (Apple Silicon M4):** Executes lock-free shared memory IPC, formal SMT invariant checks, and Merkle directed acyclic graph (DAG) state transitions.
2. **Tensor Plane (Windows 11 x86_64 Node):** Houses large model weight files (14.64 GB across 11 models) and serves inference requests across the local network, isolating the primary workstation from memory saturation and disk thrashing.

The goal of this evaluation is to establish verifiable throughput, latency, and state isolation boundaries without theoretical speculation or vendor-biased assumptions.

---

## 2. Architecture & Workload Partitioning

```
+-------------------------------------------------------------------------------------------------------+
|                                    XORAS::OS DUAL-PLANE ARCHITECTURE                                  |
+-------------------------------------------------------------------------------------------------------+
|                                                                                                       |
|   +-----------------------------------------------+       +---------------------------------------+   |
|   |         NODE A: CONTROL PLANE (macOS M4)      |       |     NODE B: TENSOR PLANE (Win11 x86)  |   |
|   |                                               |       |                                       |   |
|   |  - POSIX Lock-Free SHM (278k ops/sec)         |  LAN  |  - 11 Models Offloaded (14.64 GB)     |   |
|   |  - Z3 SMT Formal Invariant Gating             | <===> |  - Streaming Inference (21.09 tps)    |   |
|   |  - 14-Gate Blackbox Verification Gauntlet     | Socket|  - Time-To-First-Token: 493.9 ms      |   |
|   |  - Context Lineage Merkle DAG Engine          |       |  - Network Packet Loss: 0.0%          |   |
|   |  - Atomic Saga Rollback (12.8 µs)             |       |  - Workstation RAM Overhead: 0.0 GB   |   |
|   +-----------------------------------------------+       +---------------------------------------+   |
|                                                                                                       |
+-------------------------------------------------------------------------------------------------------+
```

### Partitioning Rules:
- **Zero Local Model Bloat:** The M4 developer workstation maintains 0.0 GB of static GGUF weight files, avoiding swap memory usage and unified RAM contention.
- **Hardware Taint Gating:** Untrusted candidate signals (`0xDEAD0000`) cannot update the canonical Merkle DAG until verified by invariant gates and promoted to decision status (`0xBEAF0000`).
- **Fail-Closed Fallback:** In the event of network disruption to the Windows node, the control plane rejects partial completions, rolls back pending transactions via Saga inverses, and logs the incident to the quarantine ledger.

---

## 3. Empirical Test Results

Testing was conducted using local benchmarking harnesses on both nodes under concurrent workload conditions.

### 3.1 Side-by-Side System Matrix

| Dimension / Metric | Node A: Control Plane (Apple Silicon M4) | Node B: Tensor Plane (Windows 11 Bare Metal) | Notes & Evaluation |
| :--- | :--- | :--- | :--- |
| **Assigned Roles** | State tracking, invariant proofs, audio engine | Weight storage, off-grid embeddings, LLM inference | Clean functional separation |
| **Memory Architecture** | Unified LPDDR5X (Zero-Copy L1/SIMD) | Host DDR5 RAM + GPU VRAM | Zero local workstation paging |
| **Peak Throughput** | **278,165.36 ops/sec** (POSIX SHM ring buffer) | **21.09 tokens/sec** (`qwen2.5:1.5b` streaming) | 26,000 tasks finished in 93.47 ms |
| **Formal Safety Check** | **Z3 SMT Prover = UNSAT (1.43 ms)** | 2-of-3 BFT consensus confirmed | Bounded circular buffer safety |
| **14-Gate Gauntlet** | **14 / 14 Gates Passed** (`GOLDEN-013` admitted) | Operational across LAN link (`192.168.1.211`) | Zero invariant failures |
| **L1 Cache Miss Ratio** | **0.84% L1 Miss** (Target: < 1.00%) | N/A (Weights decoupled from control plane) | 128-byte cache-line alignment |
| **State Pollution** | **0.00000%** (8 of 8 Merkle nodes verified) | 0 candidate leaks into canonical ledger | Strict quarantine enforcement |
| **Rollback Latency** | **12.8 µs** Saga hardware state inversion | Socket timeout threshold ($t = 10.0\text{s}$) | Immediate failure recovery |

---

## 4. Subsystem Verification Details

### 4.1 Lock-Free POSIX Shared Memory Concurrency
- **Implementation:** Pre-compiled native dynamic library (`core/ops/native/libshm_ring_buffer.dylib`) mapped via POSIX `shm_open` and `mmap`.
- **Test:** Burst of 26,000 simulated worker state updates distributed across 16 concurrent operating system threads.
- **Measured Result:** Completed in **93.47 ms**, yielding **278,165.36 operations/second** with zero mutex stalls or file-lock contention.

### 4.2 Z3 SMT Invariant Containment
- **Implementation:** Python Z3 SMT solver harness (`core/ops/verification/z3_shm_ring_buffer_proof.py`).
- **Safety Property:** Formally proving that under circular write increments with capacity $C = 4096$ and stride $S = 3200\text{B}$, pointer arithmetic cannot cause out-of-bounds memory writes or L1 cache-line misalignments.
- **Result:** The solver returned **UNSAT (Unsatisfiable)** in **1.43 ms**, proving the absence of buffer overflow states across all inputs.

### 4.3 14-Gate Verification Gauntlet
- **Implementation:** `core/ops/discernment/fourteen_gate_blackbox_gauntlet_512.py`.
- **Scope:** 14 automated invariant gates spanning cryptographic signatures (Ed25519), anti-replay nonces, strict typestates, L1 cache miss bounds, and Byzantine quorum thresholds.
- **Result:** **14/14 gates passed**. Hallucination index measured at **0.20%**, and groundedness measured at **97.60%**. Admitted to the Golden List under record `GOLDEN-013`.

### 4.4 Windows Tensor Plane Performance
- **Model Storage:** 11 models totaling **14.64 GB** resident on disk, including `sovereign-hermes:latest` (8.0B), `llama3.2:latest` (3.2B), `qwen2.5:1.5b` (1.8B), and `nomic-embed-text:latest` (137M).
- **Inference Benchmark (`qwen2.5:1.5b`):**
  - Prompt evaluation throughput: **77.59 tokens/second**
  - Streaming completion throughput: **21.09 tokens/second**
  - Time-to-First-Token (TTFT): **493.9 ms** across local network
  - Total stream round-trip: **1.39 seconds** (19 tokens)
  - Physical network link: **0.0% packet loss**, mean RTT **52.42 ms**

---

## 5. Failure Modes, Edge Cases & Limitations

1. **Network Disconnection / High Latency Spikes:**
   - *Behavior:* If physical LAN connectivity between M4 and Windows drops, the control plane enforces a fail-closed timeout at $t = 10.0\text{s}$, drops incomplete inference streams, and executes an atomic Saga rollback in $12.8\ \mu\text{s}$.
   - *Limitation:* While state integrity is preserved with zero pollution, inference capabilities remain offline until LAN sockets re-establish.
2. **Cold Load Latencies on Tensor Node:**
   - *Behavior:* Initial invocation of an unbuffered model on the Windows node requires disk-to-RAM paging (taking 15–25 seconds for an 8B model). Once warm in memory, response latency drops to the sub-500 ms TTFT baseline.
3. **Hardware Stride Alignment:**
   - *Behavior:* Payloads must adhere to 128-byte cache boundaries to maintain the measured 0.84% L1 miss rate. Unaligned inputs are automatically repacked by the memory allocator, adding ~0.3 µs per misaligned transaction.

---

## 6. Documented Citations & References

1. **Castro, M., & Liskov, B. (1999).** Practical Byzantine Fault Tolerance. *Proceedings of the Third Symposium on Operating Systems Design and Implementation (OSDI)*, 173–186.
2. **De Moura, L., & Bjørner, N. (2008).** Z3: An efficient SMT solver. *Tools and Algorithms for the Construction and Analysis of Systems (TACAS)*, LNCS 4963, 337–340.
3. **Merkle, R. C. (1987).** A digital signature based on a conventional encryption function. *Advances in Cryptology — CRYPTO '87*, LNCS 293, 369–378.
4. **IEEE Std 1012-2016.** IEEE Standard for System, Software, and Hardware Verification and Validation. *IEEE Computer Society*.
5. **POSIX IEEE Std 1003.1-2017.** Standard for Information Technology — Portable Operating System Interface (POSIX) Base Specifications, Issue 7.

---

## 7. Conclusion & Operational Status

The dual-plane division between the Apple Silicon M4 Control Plane and the Windows 11 Tensor Plane satisfies all technical requirements:
- Deterministic, lock-free operations execute locally at microsecond latencies without workstation storage bottlenecks.
- Heavy model inference is offloaded over physical LAN with zero observed packet loss and predictable token rates.
- State verification remains mechanical, reproducible, and mathematically bounded.

**Verification Disposition:** `[0xBEAF0000]` Promoted. Full ceiling passing criteria verified.
