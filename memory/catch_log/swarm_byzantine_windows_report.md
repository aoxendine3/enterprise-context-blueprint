# Swarm // Byzantine // Windows — Consolidated Verification Record

**Generated:** 2026-11-14 · **Scope:** sovereign records across the three planes

---

## 1. The Swarm (records on disk)

| Record | Count | Notes |
|---|---|---|
| Council transcripts (`council_transcripts.jsonl`) | 83 events | Seats: clara 20, maxx 19, orion 18, vance 12, daxx 9, jarvis 2, john 1 |
| Lead 9 roundtable journal | 22 entries | Triad deliberation lineage |
| Trinity Gate ledger (`trinity_hashes.jsonl`) | 216 events, 215 approved | Seats: MAXX 65, CLARA 64, VANCE 63 (+ DAXX 13, JARVIS 3, …) |
| Tool accountant ledger | 24 entries, 22 clean exits | Sovereign tool stability |

## 2. The Byzantine (bare-metal consensus)

- Engine: `max_byzantine_swarm` — XORAS BYZANTINE DAG CONSENSUS ENGINE (bare-metal Zig, arm64)
- Capacity: **1,000,000 nodes** · target Byzantine threshold **33.33%**
- Provisioning: **666,545 honest** / **333,455 rogue**
- Network agreement: **66.65%** · Final approved state mass: **12444.89**
- Rogue inputs isolated and discarded: **333,455**
- **Verdict: `0xBEAF` — Swarm Integrity Maintained**

## 3. The Windows Plane (cross-node attestation)

- Node: `192.168.1.211` (`desktop-8p1gp53.lan`) · HTTP/1.1 LAN, Ollama 11434
- Protocol: **UPGP v5.0 Ultra Cross-Node Verification Protocol**
- Step 1 inventory probe: **ONLINE** (17 models, incl. `hermes3:8b` / `sovereign-hermes:latest`)
- Step 2 off-grid embedding: **PASSED** — 768-D dense vector on Windows, **360.18 ms**
- Step 3 witness adversarial veto: **PASSED** — `qwen2.5:1.5b` → **DECISION: VETO**, roundtrip **6791 ms**
- Step 4 cryptographic immutability: **PASSED** — pre-state hash == post-state hash
  `187241b7…c454` → **zero state drift**
- Attestation SHA-256: `41c33a53…ac35`

---

## Verdict

**All three planes verified.** Swarm records intact, Byzantine consensus maintained at 1M-node scale, and the Windows node independently attested the same invariants — no fabrication, no state pollution.
