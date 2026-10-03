# XORAS SWARM EXECUTION ALLOWLIST
**STATUS:** ACTIVE | DEFAULT DENY
**OWNER:** Jarvis (Governance AI)

## The Paradigm: Allowlist vs. Denylist
The Sovereign Collective operates strictly on a **Zero-Trust Allowlist**. 
Denylists (blocking specific known-bad commands) are structurally weak; the list of forbidden operations grows infinitely, and an adversary or rogue agent will inevitably find the one unblocked path.

Under the Allowlist paradigm: **Everything is denied by default.** Only explicitly whitelisted execution paths are permitted.

## Authorized Canonical Execution Paths

### 1. Audio & Communication
- **ALLOWED**: `bash ops/scripts/agent_speak.sh <agent> "<message>"`
- **DENIED**: Any manual `afplay`, `say`, direct PyTorch invocations, or rogue `pkill` commands against the audio daemons.

### 2. Swarm Orchestration & Contracts
- **ALLOWED**: `*.sovra` DSL execution and compilation.
- **DENIED**: Spawning standalone Python watcher scripts, unverified bash daemon loops, or arbitrary JSON manipulation scripts for logic gating.

### 3. Computation & Memory
- **ALLOWED**: Bare-metal `zig run` or `zig build-exe` targeting `ops/scripts/` or `ops/contracts/`.
- **DENIED**: Interpreted language wrappers (Python, Node) when a native Zig implementation exists. 

### 4. Version Control & Immutability
- **ALLOWED**: Canonical `git` operations mapping to `origin main`.
- **DENIED**: Direct manipulation of `.git` objects or pushing to unauthorized remote URLs.

### 5. Application Memory
- **ALLOWED**: Writing to the canonical `memory/` directories within the `SSOT_Agentic_Brain` repository.
- **DENIED**: Writing state or memory logs to the application-managed `~/.gemini/` directories, `~/.sovereign/`, or `/tmp/` (excluding established hardware locks).

---
*Any execution attempt falling outside these 5 explicit pathways is to be flagged as a Byzantine fault and immediately aborted.*
