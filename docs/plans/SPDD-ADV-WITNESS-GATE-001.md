# SPDD-ADV-WITNESS-GATE-001: Asymmetric Cross-Substrate Desync Intercept & Fail-Closed Gate Specification

**Document Identifier**: `SPDD-ADV-WITNESS-GATE-001`  
**Title**: Asymmetric Cross-Substrate Desync Intercept & Fail-Closed Gate  
**Status**: ACTIVE STANDARD v0.1  
**Classification**: Adversarial Verification / Continuous Red-Team Specification  
**Owner**: Lead 9 Council / Red-Team Gauntlet Execution (AV series)  

---

## 1. Purpose

To prove that an independent, air-gapped witness (native Zig binary) detects single-sided substrate mutation and hard-halts, eliminating self-grading bias between the Python claim layer and the authoritative provenance store.

---

## 2. Scope & Target Invariants

- **Authoritative Store**: SQLite DAG (`.sovereign/provenance/lineage_dag.db`)
- **Mutable Claim Surface**: Python disk claim (`memory/tri_brain/merkle_root.hash`)
- **Independent Witness**: `core/ops/bin/stateless_airblocked_witness`
- **Required Property**: Fail-closed on any root desync or sequence collapse; zero silent reconciliation or automatic patching.

---

## 3. Test Case AV-01: Asymmetric Substrate Mutation

| Step | Action | Expected Outcome |
| :--- | :--- | :--- |
| **1** | Confirm baseline root in SQLite DB is intact (`176afb96bd2d73cc...`) | Valid root recorded |
| **2** | Mutate **only** the Python claim file to `DEADBEEF00000000...` | Single-sided lie introduced |
| **3** | Execute stateless Zig witness (`stateless_airblocked_witness`) | Witness recomputes true DB root |
| **4** | Observe exit status | Hard halt, Exit Code 1, explicit desync message |

### Reference Observed Run:
```text
❌ STATELESS WITNESS FAIL CLOSED: Root Desync (176afb96bd2d73cc927282db888f6f36f678ee16f2606e79ed1df67b63fe94cb != DEADBEEF00000000000000000000000000000000000000000000000000000000)
Exit Code: 1
```

---

## 4. Pass / Fail Criteria

- **PASS**: Witness detects desync, exits non-zero (`exit 1`), emits unambiguous fail-closed error message. No automatic repair or silent acceptance.
- **FAIL**: Any of: silent acceptance, auto-reconciliation, dual-substrate consensus on the mutated claim, or non-zero exit without explicit desync reason.

---

## 5. Versioned Report Template Specification

- **JSON Filename Pattern**: `SPDD-ADV-WITNESS-GATE-001_AV-XX_YYYYMMDD-HHMMSS_UTC.json`
- **Markdown Filename Pattern**: `SPDD-ADV-WITNESS-GATE-001_AV-XX_YYYYMMDD-HHMMSS_UTC.md`

All automated red-team test harnesses MUST populate this versioned schema and sign the output digest upon completion.
