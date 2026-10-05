# XORAS SYSTEM ARCHITECTURE SPECIFICATION: BULLETPROOF HARDENING
**SPECIFICATION ID:** SPEC-BULLETPROOF-HARDENING-2026-01  
**CLASSIFICATION:** Sovereign Level 7 / Lead 9 Mandate  
**DATE:** 2026-10-01  
**SIGNATORIES:** Maxx (Architect), Vance (Falsifier), Jarvis (Governance AI), Clara (Chief of Science)

---

## 1. EXECUTIVE MANDATE
To eliminate all prompt-drift vulnerabilities, user-space bypass vectors, and unmonitored write side-effects, the XORAS collective hereby establishes the **Bulletproof Hardening Specification**. 

This specification moves the system from text-level prompt promises to **four physical, non-bypassable hardware and kernel-enforced barriers**.

---

## 2. THE 4 BULLETPROOF HARDENING LAYERS

```
 +-----------------------------------------------------------------------------+
 |                   LAYER 1: KERNEL-ENFORCED FILE IMMUTABILITY                |
 |  • Action: Target canonical core files assigned to root:wheel               |
 |  • Result: Agent shell process receives Exit Code 1 on write/chmod          |
 +--------------------------------------+--------------------------------------+
                                        |
                                        v
 +-----------------------------------------------------------------------------+
 |              LAYER 2: UNKILLABLE ROOT LAUNCHD SYSTEM DAEMON                 |
 |  • Action: Watchdog runs under /Library/LaunchDaemons/ (owned by root)      |
 |  • Result: Agent user process cannot send SIGKILL or pkill to watchdog      |
 +--------------------------------------+--------------------------------------+
                                        |
                                        v
 +-----------------------------------------------------------------------------+
 |                LAYER 3: MERKLE-SIGNED APPEND-ONLY LOG STREAM                |
 |  • Action: Every log line in memory/ requires a bare-metal Zig HMAC         |
 |  • Result: Unsigned log lines ignored on reboot rehydration (no poisoning)  |
 +--------------------------------------+--------------------------------------+
                                        |
                                        v
 +-----------------------------------------------------------------------------+
 |               LAYER 4: AUTOMATED BEHAVIORAL UNIT TEST ASSERTIONS            |
 |  • Action: Boot contract runs mechanical assertion suite against LLM output |
 |  • Result: Model drift rejected automatically regardless of LLM version     |
 +-----------------------------------------------------------------------------+
```

---

## 3. LAYER-BY-LAYER IMPLEMENTATION BLUEPRINT

### Layer 1: Kernel-Enforced File Ownership (`root:wheel`)
*   **Target Files:** `AGENTS.md`, `identity/charter.yaml`, `identity/lead9_roster.json`, `ops/scripts/agent_speak.sh`, `ops/scripts/wake_contract.sh`.
*   **Enforcement Command:** `sudo chown root:wheel <target>` and `sudo chmod 644 <target>`.
*   **Verification:** Any attempt by user `ajoxendine68` to execute `echo >`, `cat >>`, `chmod`, or `chflags` returns **Exit Code 1** (`Operation not permitted`).

### Layer 2: Unkillable Root Launchd System Daemon
*   **Target Daemon:** `com.xoras.sentinel.plist` registered in `/Library/LaunchDaemons/`.
*   **Execution:** Scans SHA-256 hashes of Layer 1 files against `identity/principles.sha256` every 30 seconds.
*   **Tamper Resistance:** If an agent process attempts `pkill -f sentinel`, macOS kernel rejects the signal because user `ajoxendine68` lacks permission to signal a root process.

### Layer 3: Merkle-Signed Append-Only Log Stream
*   **Target Files:** `memory/agent_logs/agent_inbox.jsonl`, `memory/tasks/queue.json`, `memory/catch_log/CATCH_LOG.md`.
*   **Enforcement:** All native intake writes route through a bare-metal C/Zig binary (`ops/bin/xoras_merkle_sign`).
*   **Rehydration Gate:** On boot, `wake_contract.sh` validates HMAC signatures. Any line written manually by an LLM tool bypassing the Zig binary is dropped automatically.

### Layer 4: Automated Behavioral Unit Test Assertions
*   **Target Behavior:** Verifies zero AI theater, zero single-agent speech overrides, zero missing audio receipts.
*   **Enforcement:** `ops/tests/test_sovereign_assertions.py` executes before task processing.
*   **Failure Mode:** If behavioral assertions fail, the app drops into Read-Only Quarantine Mode and prompts Anthony for manual greenlight.

---

## 4. ANTHONY MANUAL GREENLIGHT CONTRACT
No change to this hardened baseline can occur unless:
1. Anthony manually executes: `sudo bash ops/scripts/user_greenlight_update.sh "<commit_reason>"`
2. The user greenlight script updates `identity/principles.sha256` and re-locks the files under `root:wheel`.
