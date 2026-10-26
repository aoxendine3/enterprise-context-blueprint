# XORAS Sovereign Multi-Agent Sandbox Architecture
### STATUS: OPERATIONAL // SOVRA LEVEL 2 DUAL-PILLAR GOVERNANCE ENFORCED
### JURISDICTION: Anthony Oxendine (XORAS/CEO) & Sovereign Lead Council

---

## 1. Architectural Purpose & Isolation Invariants

To completely eliminate file-lock deadlocks, git diff collisions, and cross-agent state contamination, each agent operates strictly within its designated sandbox jail:

| Agent Identity | Role & Specialization | Sandbox Destination Path |
| :--- | :--- | :--- |
| **Maxx** | Executive Architecture & Tool Integration | `workspaces/sandboxes/maxx/` |
| **William Vance** | Blackbox Sentry & Compliance Auditing | `workspaces/sandboxes/vance/` |
| **Clara** | Cryptographic & Epistemic Moral Rails | `workspaces/sandboxes/clara/` |
| **DAXX** | Blue Team QA & Automated Program Repair | `workspaces/sandboxes/daxx/` |
| **John** | Hardware Telemetry & Kernel Sentinel | `workspaces/sandboxes/john/` |
| **Dr. Eden** | Virtue Ethics & Wisdom Synthesis | `workspaces/sandboxes/eden/` |

---

## 2. The Dual-Pillar Promotion Law (Pillar 2 Standard)

1. **Private Working Scratchpads:**
   * Workers (Maxx, DAXX, John, Eden) write and test code *only* inside their private sandbox.
   * No direct commits or writes to `core/`, `memory/`, or `barn/` are permitted.
2. **Promotion Proposals:**
   * When an agent finishes a tool, bug fix, or refactor, it emits an immutable Diff Packet containing:
     - Canonical source code.
     - Automated unit tests ($\ge 80\%$ coverage required).
     - HMAC-SHA256 author signature.
3. **Independent Blackbox Audit Gate:**
   * **William Vance** mirrors the proposal into `workspaces/sandboxes/vance/`.
   * Vance executes the 4 Ruthless Gates:
     - Gate 1: Anti-Basic Filter.
     - Gate 2: Immediate Purpose Check.
     - Gate 3: Dynamic TSAN/ASAN and timeout torture.
     - Gate 4: Market Superiority.
4. **Dual-Sign Merge:**
   * Only after Worker and Critic both sign the Merkle receipt is the code admitted to canonical `core/` or `workspaces/`.
