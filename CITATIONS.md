# Canonical Academic & Systems Citation Registry

If you reference, benchmark against, or integrate the XORAS architecture, formal SMT2 proofs, or concurrency models in peer-reviewed research, technical reports, or production platforms, please use the standardized citations below.

---

## 1. Unified Architecture Citation (BibTeX)

```bibtex
@techreport{oxendine2026sovereign,
  author       = {Anthony Oxendine and {The Sovereign Lead 9 Council}},
  title        = {The Sovereign Triad: High-Throughput Concurrency, Formal Verification, and Epistemic Provenance for Autonomous AI Agent Swarms},
  institution  = {XORAS Systems},
  number       = {XORAS-TR-2026-001},
  year         = {2026},
  month        = {October},
  url          = {https://github.com/aoxendine3/enterprise-context-blueprint},
  note         = {Open-source reference implementation and machine-checked formal proofs}
}
```

---

## 2. Component-Specific Citations

### A. MTPO: Concurrency & 3-Phase Saga Engine
```bibtex
@inproceedings{oxendine2026mtpo,
  author       = {Anthony Oxendine and Clara and {XORAS Systems}},
  title        = {MTPO: Zero-Abort Multi-Threaded Pipeline Orchestration and Monotonic Pre-Order Invariants for Agent Inference Swarms},
  booktitle    = {Systems Architecture & Concurrency Proceedings},
  year         = {2026},
  url          = {https://github.com/aoxendine3/mtpo},
  note         = {Machine-checked in Z3 SMT-LIB v2 (unsat)}
}
```

### B. MARS: 14-Gate Gauntlet & Blackbox Supervisor
```bibtex
@techreport{oxendine2026mars,
  author       = {Anthony Oxendine and Maxx and Vance and {XORAS Systems}},
  title        = {MARS: Model-Agnostic Reasoning Supervisor and the 14-Gate Sovereign BBQ Falsification Gauntlet},
  institution  = {XORAS Systems},
  year         = {2026},
  url          = {https://github.com/aoxendine3/mars}
}
```

### C. REASONS: Context Lineage Merkle DAG Engine
```bibtex
@techreport{oxendine2026reasons,
  author       = {Anthony Oxendine and Daxx and {XORAS Systems}},
  title        = {REASONS: Epistemic Provenance, Anti-Replay Invariants, and Policy-as-Graph in Autonomous Context Networks},
  institution  = {XORAS Systems},
  year         = {2026},
  url          = {https://github.com/aoxendine3/reasons}
}
```

### D. Dual-Plane Separation (NASA Technical Memorandum)
```bibtex
@techreport{xoras2026dualplane,
  author       = {{The Sovereign Lead 9 Council}},
  title        = {Dual-Plane Architectural Separation: Formal SMT Control Plane vs. Probabilistic Streaming Tensor Plane (UDP 11434)},
  institution  = {XORAS Systems / NASA V\&V Technical Memorandum Series},
  number       = {XORAS-TM-2026-037},
  year         = {2026},
  month        = {October},
  url          = {https://github.com/aoxendine3/enterprise-context-blueprint/blob/main/docs/audits/XORAS_037_DUAL_PLANE_SEPARATION_CONTROL_VS_TENSOR_UDP11434.md}
}
```

---

## 3. Standard Text Citations

### USENIX / Chicago Style
> Oxendine, Anthony, and The Sovereign Lead 9 Council. 2026. "The Sovereign Triad: High-Throughput Concurrency, Formal Verification, and Epistemic Provenance for Autonomous AI Agent Swarms." Technical Report XORAS-TR-2026-001, XORAS Systems. https://github.com/aoxendine3/enterprise-context-blueprint.

### IEEE Style
> A. Oxendine and The Sovereign Lead 9 Council, "The Sovereign Triad: High-Throughput Concurrency, Formal Verification, and Epistemic Provenance for Autonomous AI Agent Swarms," XORAS Systems, Tech. Rep. XORAS-TR-2026-001, Oct. 2026. [Online]. Available: https://github.com/aoxendine3/enterprise-context-blueprint.

### ACM Style
> Anthony Oxendine and The Sovereign Lead 9 Council. 2026. The Sovereign Triad: High-Throughput Concurrency, Formal Verification, and Epistemic Provenance for Autonomous AI Agent Swarms. Technical Report XORAS-TR-2026-001. XORAS Systems. https://github.com/aoxendine3/enterprise-context-blueprint.

---

## 4. Cryptographic Proof & Ledger Verification Anchors

To ensure academic and forensic reproducibility, all citations are cryptographically bound to the following verified bitstrings:

| Artifact | Location | SHA-256 Digest |
| :--- | :--- | :--- |
| **MTPO Pre-Order Proof** | `proofs/mtpo_preorder_invariant.smt2` | `e971295fc3bbdb18e24ad16cb179b5c3258c70757a3e6f98ef421ef28ba6c63b` |
| **UPGP Containment Proof** | `core/ops/security/upgp_containment_proof.smt2` | `81cb284d499c586446f7392f7768c039d707f633f40a3101d88839c880e45c96` |
| **Clean-Room Toolchain** | `zig-aarch64-macos-0.16.0.tar.xz` | `b23d70deaa879b5c2d486ed3316f7eaa53e84acf6fc9cc747de152450d401489` |
| **Evidence Ledger Root** | `memory/catch_log/evidence_ledger.jsonl` | Height: 34 Rows (Verified with Ed25519) |
