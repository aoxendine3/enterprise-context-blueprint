---
name: epistemic-provenance-recovery
description: Epistemic Disconnect Recovery Protocol & Zero-Trust Knowledge Object Committal Law for XORAS/Maxx/DAXX Swarm Agents.
---

# Epistemic Provenance Recovery & Zero-Trust Committal Law

## Operational Mandate
When the system encounters an **Epistemic Disconnect** between physical reality (files on disk) and provenance state (records in `world_file.db` / Merkle DAG), agents must execute the **Unrecorded Asset Recovery Loop** to transform orphaned raw files into trusted **Knowledge Objects**.

---

### 1. Core Principles & Definitions

* **Raw Files vs. Knowledge Objects**: A file on disk is not a trusted asset until it is transformed into a **Knowledge Object** carrying defined metadata attributes:
  - **Identity**: Unique canonical ID & SHA-256 hash.
  - **Version**: Immutable semantic/commit version.
  - **Origin**: Authoring agent ID & execution context.
  - **Relationships**: Dependency graph pointers.
  - **Trust Score**: Hardware taint status (`0xBEAF0000` decision vs `0xDEAD0000` candidate).
  - **Decision Lineage**: SPDD REASONS Canvas & Ed25519 signature audit trail.
* **Zero-Trust Fail-Closed Security**: Unrecorded files are treated as untrusted, foreign, or malicious injections until formally audited and committed to `world_file.db`.
* **Atomic Tool-Call Logging Invariant**: File mutations cannot take effect without committing the corresponding decision trace to `world_file.db` in the exact same execution step.

---

### 2. The Three-Step Unrecorded Asset Recovery Loop

```
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                   THE UNRECORDED ASSET RECOVERY LOOP                    │
 ├─────────────────────────────────────────────────────────────────────────┤
 │ 1. PHYSICAL DISK RECONNAISSANCE ──► Run `list_dir` / `git status` in    │
 │                                     `/core/`, `/scratch/`, and `/barn/` │
 ├─────────────────────────────────┼───────────────────────────────────────┤
 │ 2. POST-MORTEM INTENT RECON.    ──► Read physical code & reconstruct     │
 │    (SPDD `/spdd-sync` Pass)     │ REASONS Canvas & Decision Trace       │
 ├─────────────────────────────────┼───────────────────────────────────────┤
 │ 3. BLACKBOARD COMMITTAL         ──► Write Knowledge Object to `world.db`│
 │                                     & sign Ed25519 audit checkpoint     │
 └─────────────────────────────────┴───────────────────────────────────────┘
```

#### Step 1: Physical-Plane Disk Reconnaissance
DAXX Master Engine or a designated worker bypasses conversational memory and executes un-gated physical scans (`list_dir`, `git status`, `rg`) across `/core/`, `/scratch/`, and `/barn/` to locate physical source code files.

#### Step 2: Post-Mortem Intent Reconstruction (SPDD `/spdd-sync` Pass)
Inspect the physical source files and reconstruct their **REASONS Canvas**:
- **R**equirements: Target problem statement & invariants.
- **E**ntities: Component schemas & symbol definitions.
- **A**pproach: Architectural solution & execution flow.
- **S**afeguards: Verification gauntlets, Z3 proofs & error handling.
- **O**utput: Deliverable artifacts & API endpoints.
- **N**on-functional: Latency, memory alignment & thread safety.
- **S**ignature: Cryptographic Ed25519 hash.

#### Step 3: Blackboard Registration & Checkpoint Signing
Commit the reconstructed metadata into `world_file.db` (and Merkle DAG), assign an **Ed25519 cryptographic signature**, and log the receipt in `memory/catch_log/provenance_recovery.log`.

---

### 3. Permanent Architectural Prevention

Every file mutation tool call must be paired atomically with a blackboard write:
1. Mutate physical file on disk.
2. Generate SHA-256 hash & Ed25519 signature.
3. Write Knowledge Object record to `world_file.db` blackboard table `knowledge_objects`.
4. Screen through 7th-Layer Guard Membrane before finalizing turn.
