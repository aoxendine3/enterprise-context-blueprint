# XECRS: Xoras Evidence-Centered Reporting System
**Version:** 1.0.0
**Status:** ACTIVE SPECIFICATION
**Immutable Rule:** All system reports, audits, and gauntlet outcomes MUST follow this structure. Any report missing these sections will be physically rejected by `ops/watchdog/xecrs_schema_validator.py`.

## 01. Report Identity
- **Report ID:** XECRS-[ID]
- **Target/Subject:** [What is being audited/tested]
- **Execution Triad:** [Agent Names]

## 02. Executive Summary
- **Objective:** [Plain English]
- **Verdict:** [QUALIFIED / KILLED / OPEN]

## 03. Claim Ledger
Every material statement must be explicitly listed here with its status:
- `[VERIFIED]` - Supported by a concrete execution result/artifact.
- `[CORROBORATED]` - Supported by multiple project records but not independently re-executed.
- `[REPORTED]` - A document states the result, but raw evidence is unavailable.
- `[OPEN]` - Evidence needed to establish the claim is not demonstrated.

## 04. Verification Matrix
| Component | Verification Command | Exit Code | Script Digest | Doc Digest | Status |
| --- | --- | --- | --- | --- | --- |
| [Target] | `[Command]` | `[0]` | `[Hash]` | `[Hash]` | `[Pass/Fail]` |

## 05. Evidence Graph
Map the relationships:
`[CLAIM]` -> `[REQUIREMENT]` -> `[TEST COMMAND]` -> `[RAW RECEIPT JSON]` -> `[MERKLE ROOT HASH]`

## 06. Adversarial / Negative Testing
- Describe the exact tests run to *break* the system. What happens when the expected condition is deliberately broken?
- Include the Sentinel Mutation Catch Rate (e.g., 100%).

## 07. Cryptographic Receipts
- **Taint State:** `[0xDEAD0000 / 0xBEAF0000]`
- **Merkle Root (SHA-256):** `[64-char Hash]`

## 08. Disagreement & Discernment Record
- Explicitly record any internal Triad disputes (e.g., Vance rejecting a premise, Clara defending a human-in-the-loop exception).
