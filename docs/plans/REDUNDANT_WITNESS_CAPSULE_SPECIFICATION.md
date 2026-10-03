# XORAS ARCHITECTURE BLUEPRINT: REDUNDANT WITNESS & CAPSULE ISOLATION
**SPECIFICATION ID:** SPEC-REDUNDANT-WITNESS-2026-02  
**CLASSIFICATION:** Sovereign Level 7 / Lead 9 Core Specification  
**DATE:** 2026-10-01  
**SIGNATORIES:** Maxx (Architect), Jarvis (Governance AI), Vance (Falsifier), Clara (Chief of Science)

---

## 1. EXECUTIVE PRINCIPLE: THE REDUNDANT WITNESS MANDATE
A single ledger—no matter how mathematically pure—is a single point of failure if the executing process possesses file-write access to that ledger's location.

To eliminate single-ledger vulnerability and capsule corruption, the XORAS collective establishes **The Redundant Witness Architecture**:
1. **Witness A (Local SSOT Ledger):** `memory/provenance/MERKLE_EVIDENCE_TRACKER_LEDGER.jsonl`
2. **Witness B (Out-of-Band Isolated Witness):** `~/.sovereign_witness/out_of_band_merkle_witness.jsonl` (Restricted location outside workspace root)
3. **Witness C (Capsule Integrity Register):** `identity/sovereign_citizens_manifest.json` (Read-locked capsule state)

---

## 2. SYSTEM ARCHITECTURE & DUAL-WRITER FLOW

```
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                    STATE TRANSITION / ACTION EVENT                        │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │
                                        ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                BARE-METAL MERKLE DUAL-WITNESS DISPATCHER                   │
 │                • File: ops/bin/xoras_merkle_sign (Zig Binary)              │
 └───────────────────┬─────────────────────────────────────┬───────────────────┘
                     │                                     │
                     ▼                                     ▼
 ┌──────────────────────────────────────┐  ┌───────────────────────────────────┐
 │  WITNESS A (Local SSOT Ledger)       │  │  WITNESS B (Out-of-Band Witness)  │
 │  • Location: memory/provenance/      │  │  • Location: ~/.sovereign_witness/│
 │  • Enforces: In-tree provenance      │  │  • Enforces: Out-of-tree hash lock│
 └──────────────────────────────────────┘  └───────────────────────────────────┘
                                        │
                                        ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │               CONSENSUS VERIFIER (Pre-Flight Boot Contract)                │
 │  • Compares Hash(Witness A) == Hash(Witness B)                             │
 │  • IF mismatch detected: HALT EXECUTION -> ALERT ANTHONY -> REVERT FROM GIT │
 └─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. CAPSULE ISOLATION & CITIZEN MANIFEST LOCKS

1. **Citizen Capsule Boundary:** Each agent identity (`Maxx`, `Jarvis`, `Vance`, `Clara`, `Daxx`) has an assigned capsule in `identity/sovereign_citizens_manifest.json` and `Xoras_agent_cards/`.
2. **Anti-Corruption Rule:** An active agent runtime is **physically prohibited** from modifying its own agent card or another agent's capsule.
3. **Out-of-Band Verification:** Before any agent executes a high-privilege action, Witness B (`~/.sovereign_witness/`) verifies that the agent's active memory context matches its immutable capsule hash in Witness C. If an agent tries to "alter who it is inside its capsule," the out-of-band witness immediately flags **CAPSULE_CORRUPTION_DETECTED** and rejects the transition.

---

## 4. IMPLEMENTATION & PROOF STEPS

1. **Create Out-of-Band Directory:** Establish `~/.sovereign_witness/` with `0700` restricted POSIX permissions outside the workspace root.
2. **Dual-Write Logging:** Modify `ops/scripts/prompt_todo_bootstrap.py` and native intake to write state hashes synchronously to both Witness A and Witness B.
3. **Out-of-Band Reconciliation Check:** Include Witness B cross-validation in `ops/scripts/wake_contract.sh`.
