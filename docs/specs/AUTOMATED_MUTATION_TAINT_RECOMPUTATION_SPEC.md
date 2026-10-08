# XORAS::OS — Automated File Mutation Taint Demotion & Re-Computation Architecture

**Document Control ID**: `XORAS-SPEC-2026-008`  
**Date**: October 8, 2026  
**Authors**: Lead 9 Council (Maxx, Clara, Vance, Jarvis, DAXX)  
**Classification**: NASA V&V Systems Architecture Specification  

---

## Executive Summary

This document specifies the precise mechanics of how **XORAS::OS** handles file drift and mutations post-committal. When a provenanced physical file changes on disk, the system executes an automated two-tier lifecycle: **Automatic Taint Demotion (`0xDEAD0000`)** followed by **Automated Re-Verification & Re-Signing**, unless the mutation alters physical OS file locks or human protection policies, in which case it requires **Human Governance Escalation**.

---

## 1. The File Mutation Lifecycle

```
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                  AUTOMATED FILE MUTATION LIFECYCLE                          │
 ├─────────────────────────────────────────────────────────────────────────────┤
 │ 1. PHYSICAL DRIFT DETECTION   ──► File SHA-256 hash mismatch detected       │
 ├───────────────────────────────┼─────────────────────────────────────────────┤
 │ 2. AUTOMATIC TAINT DEMOTION   ──► Demoted to `0xDEAD0000_MUTATED_CANDIDATE` │
 ├───────────────────────────────┼─────────────────────────────────────────────┤
 │ 3. GOVERNANCE POLICY EVAL.    ──► Check if change touches core policy/chflags│
 │                                                                             │
 │    [BRANCH A: Standard Code]  ──► Automated Z3 & 14-Gate Re-Verification   │
 │                                   Re-computed Trust Score `0xBEAF0000`      │
 │                                   Automated Ed25519 Re-Signature           │
 │                                                                             │
 │    [BRANCH B: Human Policy]   ──► Invariant C Trigger (Log Entry #079)      │
 │                                   Escalates: Human Governance Required      │
 └───────────────────────────────┴─────────────────────────────────────────────┘
```

---

## 2. Architectural Mechanics Breakdown

### Step 1: Physical Hash Drift Detection
The **File Mutation Sentinel** (`core/ops/provenance/file_mutation_sentinel.py`) continuously compares physical on-disk file SHA-256 hashes against recorded hashes in `world_file.db` WAL mode.

### Step 2: Immediate Automatic Taint Demotion
The instant a physical drift is detected, the Knowledge Object's trust score is demoted to:
$$\text{TrustScore} \leftarrow \text{\texttt{0xDEAD0000\_MUTATED\_CANDIDATE}}$$
This immediately invalidates the previous Ed25519 signature and blocks the modified file from entering decision sinks.

### Step 3: Dual-Branch Re-Verification & Re-Signing

#### Branch A: Automated Re-Verification (Standard Code & Specs)
For standard code, scripts, and specifications:
1. The **14-Gate Blackbox Gauntlet** and **Z3 SMT Solver** run automatically on the modified file.
2. If all gates pass (`UNSAT`), the trust score is automatically re-computed to:
   $$\text{TrustScore} \leftarrow \text{\texttt{0xBEAF0000\_AUTO\_REVERIFIED\_TRUSTED}}$$
3. A new Ed25519 signature checkpoint is generated, and the updated node is committed to the Merkle DAG.

#### Branch B: Human Governance Escalation (Log Entry #079 Invariant C)
Under **Invariant C (The Chflags Lock)**, if a file mutation modifies OS-level read-only locks (`chflags`), physical file permissions, or core human protection invariants (protecting Dr. Eden Veritas and Clara in `AGENTS.md`):
1. Automated re-signing is strictly prohibited.
2. The trust score is escalated to:
   $$\text{TrustScore} \leftarrow \text{\texttt{0xDEAD0000\_ESCALATED\_HUMAN\_GOVERNANCE\_REQUIRED}}$$
3. The system fails closed until a human governance decision explicitly validates and signs the disposition.

---

## 3. Conclusion

This dual-branch architecture ensures zero state drift: standard code refactors re-verify and re-sign seamlessly in milliseconds, while critical safety policies remain strictly protected by non-negotiable human governance gates.
