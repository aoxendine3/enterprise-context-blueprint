# XORAS Telemetry Cockpit — Security Model, Gap Analysis, and Hardening Roadmap

Status: **LIVING THREAT MODEL**. The threat analysis below remains the plan;
the implementation status is tracked here so nothing is mistaken for a claim.

Implementation status (2026-11-16):
- **Closed:** detached Ed25519 bundle signature + browser verification with a
  pinned SPKI public key; enforced ≥80% coverage gate; adapter input caps;
  writer+cockpit gates wired into `reality_gate.sh` (now 7/7 PASS); poisoned
  Merkle claim repaired and BBQ self-poisoning stopped; signed known-good
  source manifest with live drift detection (verified by a controlled ghost
  edit); monotonic `build_seq` with an external high-water mark; DART clearance
  tagging and credential redaction in the exporter.
- **Closed P0:** the exporter now runs `PRAGMA integrity_check`, verifies
  lineage parent linkage across the selected 300-row window, and emits a
  `LINEAGE_VERIFIED` required-slot record; a broken chain or corrupt DB refuses
  to export.
- **Remaining P1/P2:** bind the existing 2-of-3 witness/quorum machinery to
  bundle bytes, external custody of the public-key pin, runtime asset
  verification, and cross-language canonicalization golden vectors.
- **Open P1:** 2-of-3 critic quorum bound to artifact bytes (the repo has
  `trinity_gate.py`, `reconcile_witness_root.py`, `dual_witness_gate.sh` and
  `cross_model_critic.py` to reuse), external key-pin custody, runtime asset
  verification, cross-language canonicalization golden vectors.
- **Not claimed:** cryptographic authenticity from an external trust anchor,
  true process/key isolation, production readiness while the repo's gates were
  failing (they now pass, but the open P0 items still stand).
It records the trust boundaries, the attacks we have actually considered, what
already exists in the repo, and the ordered work required to reach the ultimate
state. Every item is written so a critic can verify it rather than take it on
faith.

---

## 1. Trust boundaries

```
   ┌──────────────────────── HOST / KERNEL ────────────────────────┐
   │  agent processes (same OS user today)                         │
   │  ├─ writer/exporter (PRODUCER)                                │
   │  ├─ critic/verifier (must become INDEPENDENT)                 │
   │  └─ ghost writers (unauthorised processes on the same user)    │
   │  SSOT: receipts/*.json, world_file.db, *.jsonl, audit chains   │
   │  keys: .sovereign/crypto_keys/... (same-user readable today)   │
   ├────────────────────── BUILD BOUNDARY ─────────────────────────┤
   │  exporter → signer → trust root → asset lock → browser bundle  │
   ├──────────────────── DISTRIBUTION BOUNDARY ────────────────────┤
   │  dist/index.html + cockpit.js + evidence-bundle.json           │
   ├──────────────────── BROWSER / RUNTIME ────────────────────────┤
   │  adapter → verifySnapshot → render (strict CSP, no network)    │
   └────────────────────────────────────────────────────────────────┘
```

Trust assumptions we currently make and must either enforce or document:

1. The host kernel/filesystem is honest (we cannot defend against root).
2. The build script and signer are honest (today they run as the same user).
3. The signing/attestation keys are not readable by the producing agent
   (**not true today**: all agent keys are under the same macOS user).
4. The browser runtime and `cockpit.js` are unmodified (client-side checks
   cannot defend against a compromised client).
5. The pin in `trust_root.js` is shipped independently of the bundle it pins
   (**not true today**: it is generated in the same build).

---

## 2. Assets to protect

| Asset | Current protection | Gap |
|---|---|---|
| Evidence bundle integrity | manifest SHA-256 + pinned digest | no cryptographic authorship |
| Bundle freshness | none | signed old bundle can be replayed |
| Writer receipts | hash-chained audit ledger | chain head not externally pinned; rollback possible |
| SSOT source files | none at export time | ghost writer can alter a receipt before export; exporter faithfully ships the lie |
| `world_file.db` lineage | copied verbatim | no `integrity_check`, no seq/parent_hash/merkle verification |
| Critic identity | none | same-user keys; `critic_id != writer_id` not yet enforced |
| Secrets / PII inside receipts | none | bundle may leak sensitive claims to every consumer |
| Dist assets | `assets.lock.json`, build-time only | no runtime verification; symlink/TOCTOU not closed in verifier |
| Gate enforcement | cockpit build only | not yet wired into `reality_gate.sh` / `verify_all_production_gates.sh` |

---

## 3. Attack surfaces and concrete gaps

### 3.1 Ghost intrusion / invisible host modification (critical)
An unauthorised process on the same user can edit a receipt, a JSONL sidecar,
or a DB row. The exporter currently reads whatever is on disk and creates a
perfectly self-consistent bundle. The pin then authenticates the poisoned
bundle. **Fix:** a signed, immutable known-good manifest of every ingested
source file (path, byte count, SHA-256, last accepted chain head). The exporter
must verify every source against it before inclusion and halt on any drift or
on any source not in the manifest. This is the single most important missing
control.

### 3.2 Rollback / replay of whole builds (critical)
`trust_root.js`, `assets.lock.json`, and the signed bundle are generated in the
same build and are not externally anchored. Restoring an older valid set
passes every current check. **Fix:** a monotonic build sequence stored outside
the repo (append-only ledger or SQLite counter with restricted permissions),
signed into the bundle as `build_seq`, verified by the adapter against a pinned
high-water mark; plus an external transparency-log/commitment for the public
key fingerprint.

### 3.3 Self-certification and key custody (critical)
All agent keys live under one OS user. `critic_id != writer_id` can be enforced
in data but the writer could still load Vance's private key. **Fix:** separate
OS user or hardware token for the critic key, `0444` attestation root, and
identity-scope guard wired into Wake Contract Stage 1. Until then the
attestation is an accountability signal, not a security boundary.

### 3.4 Side channels and TOCTOU (high)
- File double-read in the RAW gate narrows but does not remove a concurrent
  writer race. Keep atomic `os.replace` + `flock` as the primary defence.
- `fsync` durability is filesystem-dependent; document, do not claim power-loss
  safety.
- Verification ordering can leak which slot failed first; acceptable for
  diagnostics, but never expose key material or full secret-bearing claims in
  failure strings.
- WebCrypto operations are constant-time in the browser; our own JavaScript
  hash loops are not used for secrets.

### 3.5 Bundle-borne data leakage / DART egress (high)
Receipts contain arbitrary claims. The exporter copies `claims` verbatim into a
bundle intended for distribution. A secret or personal datum in a receipt
becomes public. **Fix:** attach a DART clearance to every source and every
record (PUBLIC/INTERNAL/RESTRICTED/SEALED), default fail-closed to RESTRICTED,
apply a verified downgrade/redaction operator before bundle inclusion, and
make the adapter reject any record whose clearance exceeds the bundle egress
clearance. This reuses the cage-containment doctrine already present in the
repo's Z3 proofs.

### 3.6 Denial of service in the adapter (high)
A crafted bundle with millions of records causes millions of sequential
`crypto.subtle.digest` calls in `loadBundle`. **Fix:** enforce `MAX_BUNDLE_BYTES`,
`MAX_RECORDS`, `MAX_SOURCES`, and per-field length caps before any hashing, and
return a fail-closed `BUNDLE_TOO_LARGE` reason. Apply the same caps in the
exporter (receipt count/size caps are now applied; bundle-level caps are not).

### 3.7 Database lineage integrity (high)
`lineage_nodes` is copied without verifying `S_N = S_{N-1} + 1`, parent-hash
linkage, or the signed `master_merkle_checkpoints` root. **Fix:** run
`PRAGMA integrity_check`, walk the selected lineage window, verify monotonic
sequence and parent linkage, verify the checkpoint signature, and emit a
`LINEAGE_VERIFIED` receipt that the bundle requires as a slot.

### 3.8 Weak authenticity of the pin (medium-high)
Even with a detached Ed25519 signature, the public-key pin is generated locally
and `dist/` is gitignored. **Fix:** commit a reviewed SPKI fingerprint in a
tracked file with `0444` permissions, require two-person approval to change it,
and mirror it to an external transparency log.

### 3.9 Quorum and rotation (medium)
One critic signature is a single point of failure. **Fix:** require 2-of-3
critic attestations for high-risk claims, with distinct agent keys and a
rotation/revocation record. Adapter enforces the quorum from the pinned root.

### 3.10 Runtime asset integrity (medium)
`assets.lock.json` is checked at build time only. **Fix:** serve with HTTP
`Content-Security-Policy` and Subresource Integrity headers; for `file://`
accept the residual limitation explicitly. Use `lstat`/`O_NOFOLLOW` in
`verify_assets.py` so a symlink swap cannot defeat the check.

### 3.11 Gate enforcement gap (medium)
Cockpit and writer gates are only in the cockpit build. **Fix:** wire them into
`reality_gate.sh` and `verify_all_production_gates.sh` as explicit gates with
updated counts and receipts.

### 3.12 Canonicalization drift (medium)
Three copies of `_canon`/`canonicalStringify` must stay byte-identical. **Fix:**
a single golden-vector test shared across Python and JS, run in every build.

---

## 4. Primitives that already exist and must be reused, not rebuilt

- `core/ops/provenance/evidence_ledger.py` — append-only, hash-chained,
  Ed25519-signed rows; keys in `.sovereign/crypto_keys/agents/<AGENT>/`.
- `ops/telemetry/state_assertion_gate.py` — double-read RAW verification with
  `CERTIFIED` / `FAIL_CLOSED` and `sdi`.
- `ops/tools/xoras_file_writer.py` — atomic staging/publish, flock, fsync,
  hash-chained audit, RAW post-write verification, all-suffix NFKC policy.
- `ops/security/identity_scope_guard.py` — card/charter/root pinning and
  sealed `0444` identity material.
- `core/ops/scripts/quarantine_governed_memory_poison.py` and
  `memory/catch_log/QUARANTINE_LEDGER.json` — preserve/prove/report protocol.
- `ops/scripts/sovereign_activity_trace.py` — hash-chained spans with
  before/after SHA-256.
- Z3 cage-containment proof in the blueprint — the formal basis for the DART
  egress gate in §3.5.

---

## 5. Ordered remediation

**P0 — ultimate-state blockers (must all hold before any VERIFIED claim)**
1. Signed known-good source manifest + exporter verification (§3.1).
2. Monotonic build sequence with externally pinned high-water mark (§3.2).
3. Detached Ed25519 bundle signature + independent critic attestation with
   enforced `critic_id != writer_id` (§3.3, signed payloads verified in browser).
4. DART clearance tagging and egress redaction for bundle records (§3.5).
5. Adapter input caps and database lineage integrity (§3.6, §3.7).
6. Wire writer + cockpit gates into the real production gates (§3.11).

**P1 — raises the assurance level**
7. 2-of-3 critic quorum and key rotation/revocation (§3.9).
8. Public-key fingerprint committed out of band with two-person integrity
   (§3.8).
9. Runtime asset verification and symlink-safe lock verification (§3.10).
10. Cross-language canonicalization golden vectors (§3.12).

**P2 — operational maturity**
11. SBOM and pinned toolchain versions for Python/Node/cryptography.
12. Reproducible hermetic build (container or Nix) with no network egress.
13. Continuous integrity monitoring daemon comparing SSOT to the known-good
    manifest on a 30-second pulse, emitting a signed divergence receipt.
14. Human-in-the-loop approval receipt for any promotion to VERIFIED.

---

## 6. What we will not claim

- Cryptographic authenticity without external key custody and an externally
  pinned fingerprint.
- True independence while writer and critic run as the same OS user.
- Power-loss durability beyond the filesystem's `fsync` guarantees.
- Semantic correctness: a critic recomputes bytes, not code quality or intent.
- Production readiness while the repo's own `REALITY_GATE_RECEIPT.json` reports
  `REALITY_GATE_FAIL` and the golden harness reports `pass_rate: 0.0`.

The cockpit will continue to halt until the underlying gates pass. That is the
correct behaviour; hardening the cockpit must never become a way to hide a
failing reality.
