---
name: upgp_falsification_audit
description: Zero-Trust Anti-Replay Falsification, Bit-Flip Verification, and Digit-by-Digit Audit Protocol for UPGP v5.0 Ultra.
---

# UPGP Zero-Trust Falsification & Anti-Replay Auditing Skill

## Operational Mandate
This skill provides the mandatory operational procedures, automated testing harnesses, and verification gauntlets required to falsify attestation claims, test cryptographic freshness, and audit every numerical parameter digit-by-digit across UPGP v5.0 Ultra deliverables.

---

### 1. Invariants & Rules

1. **Digit-by-Digit Traceability (Invariant F)**:
   - No numeric parameter, threshold, memory offset, or benchmark claim (e.g. 30s freshness, 290k ops/sec, 15 escape vectors, 18,432-D manifold) may exist without explicit mathematical derivation and empirical measurement.

2. **Anti-Replay & HMAC Attestation (Invariant G)**:
   - Every attestation endpoint (`http://localhost:8443/api/telemetry`) MUST require:
     - HMAC-SHA256 signature verification over state vector content.
     - Monotonically increasing nonces per client/session.
     - Timestamp freshness verification window ($\le 30$ seconds).
   - Replaying a previously valid signed payload MUST fail with `403 Forbidden` / `STALE_NONCE_OR_TIMESTAMP`.
   - Modifying a single bit in the payload MUST mutate the state badge from `SECURE` to `CORRUPTED`.

3. **Audio-First Governance & Collective Voice (Invariant H)**:
   - All state mutations and falsification audits MUST emit speech via `ops/scripts/agent_speak.sh` under the Lead 9 Council collective identity ("We", "Our").

---

### 2. Verification Gauntlet Execution Suite

#### Test A: Cryptographic Bit-Flip Falsification
Tests that the telemetry server catches bit flips and invalid signatures in real time.
```bash
python3 core/ops/scripts/test_bit_flip_falsification.py
```
*Expected Result*: Returns `Status 403` with message `INVALID_HMAC_SIGNATURE` and telemetry status shifts to `CORRUPTED`.

#### Test B: Replay Attack Freshness Falsification
Tests that a valid, captured signed payload cannot be replayed past its nonce or 30-second freshness window.
```bash
python3 core/ops/scripts/test_replay_attack_falsification.py
```
*Expected Result*: Replay payload is rejected with `Status 403` (`REPLAY_ATTACK_DETECTED`).

#### Test C: Live Telemetry Server Health Check
Verify live server status and nonce increments:
```bash
curl -s http://localhost:8443/api/telemetry | jq .
```

#### Test D: Document Link & Asset Integrity Audit
Scans all markdown documentation and HTML pages for broken links, missing assets, or outdated version strings (e.g., v3.0 references).
```bash
python3 core/ops/scripts/enforce_doc_sync_gate.py
```

---

### 3. Product Packaging & Release Verification
To build and verify the release tarball:
```bash
python3 core/ops/scripts/package_upgp_product.py
```
Outputs `dist/upgp-v4.0-ultra-sovereign-bundle.tar.gz` and verifies SHA-256 integrity.

---

### 4. Catch Log Receipt Protocol
Upon completing any audit run, record execution receipt in `memory/catch_log/upgp_falsification_audit.log`:
```json
{
  "timestamp": "ISO-8601",
  "audit_name": "upgp_falsification_audit",
  "bit_flip_status": "PASSED",
  "anti_replay_status": "PASSED",
  "doc_sync_status": "PASSED",
  "auditor": "The Lead 9 Council (Maxx / Vance / Clara)"
}
```
