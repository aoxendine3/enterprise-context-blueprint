# XORAS Telemetry Validation Cockpit

**Version: 5.0.0-rc.1 (release candidate).** Status and version align with the root
`README.md` and `version.json`.

Canonical, single-source cockpit for reading the repository's real evidence and
rendering only what is receipt-backed. It replaces the Downloads mockup
(`xoras_agent_telemetry_validation_engine (1).html`) entirely: no fake hash,
no hardcoded `passed: true`, no CDN, no inline handlers.

## One entry point

```bash
cd workspaces/telemetry_cockpit
bash build.sh
```

`build.sh` performs, in order: real evidence export -> structural verification
-> single-file runtime build -> asset lock -> full test suite. Any failure
exits non-zero. There is no second build path.

Open `dist/index.html` locally, then use **LOAD EVIDENCE BUNDLE** to select
`dist/evidence-bundle.json`. Until that file is loaded the cockpit stays in
**SIMULATION** mode and shows no backed values.

When the cockpit is served over HTTP(S) (GitHub Pages, any static server),
the same-origin sibling `evidence-bundle.json` is loaded automatically at
startup — relative path only, and every failure path stays SIMULATION. The
WebCrypto signature check remains the only trust gate; the transport is
never trusted. Over `file://` the manual LOAD button remains the only path.

## Doctrine enforced in code

1. **Single source of truth:** the repo's receipts, `world_file.db`, and JSONL
   sidecars are frozen at build time into one manifest-hashed bundle. The UI
   derives everything from that bundle and never mutates it.
2. **One entry point:** `bootstrap` in `src/app.js` wiring to
   `EvidenceAdapter.load`.
3. **One validation path:** `verifySnapshot()` is the only producer of
   `VERIFIED` / `DIVERGED` / `HALTED`.
4. **No fabrication:** a value without a source becomes `UNVERIFIED` in the
   unresolved-slots panel. There is no default pass.
5. **Fail closed:** missing evidence, manifest mismatch, invalid record, or a
   `FAIL` verdict halts the cockpit. `canMutate()` is true only for `VERIFIED`.
6. **No network:** local vendored CSS/JS, strict CSP with `connect-src 'none'`.

## Layout

```
workspaces/telemetry_cockpit/
  build.sh                     single canonical build
  README.md                    this file
  tools/export_evidence_bundle.py   real SSOT -> evidence bundle
  tools/verify_bundle.py       structural verifier
  src/crypto.js                real WebCrypto SHA-256, canonical JSON
  src/state-machine.js         fail-closed verification state machine
  src/evidence-adapter.js      only source of VERIFIED/DIVERGED/HALTED
  src/app.js                   safe DOM renderer (textContent, no innerHTML)
  dist/index.html              offline shell with CSP
  dist/cockpit.css             vendored local styling
  dist/cockpit.js              generated concatenation of src modules
  dist/evidence-bundle.json    generated from real repo data
  dist/assets.lock.json        SHA-256 of all shipped assets
  tests/*.test.mjs             crypto, state, adapter, static, bundle tests
```

## Current honest state (do not misread as completion)

The repo's own receipts currently report:

- `REALITY_GATE_RECEIPT.json` (`2026-11-16T22:03:13Z`): `REALITY_GATE_FAIL`,
  8 passed / 1 failed of 9, first failure `golden groundedness (floor metric)`;
  production `6/6`, writer/cockpit/CI-surface PASS, `3651` lineage nodes.
- `GOLDEN_GROUNDEDNESS_RECEIPT.json`: `GOLDEN_FAIL`, `pass_rate: 0.0` against an
  `80.0` floor — a blocking gate; the harness is fail-closed at 25/25 questions.
- `world_file_manifest_pointers`: zero rows, so the `ROOT_MANIFEST` slot is
  absent.

Therefore a correctly wired cockpit **must** show `HALTED`, not `VERIFIED`.
That is a successful fail-closed result, not a defect in this build. The
product is not complete until those underlying gates pass and the bundle
resolves to `VERIFIED` with zero unresolved slots.

## Authenticity

The evidence bundle carries a detached Ed25519 signature over the same
canonical bytes that produce its manifest digest. `dist/trust_root.js` pins
both the expected digest and the signing public key (SPKI base64). The adapter
verifies the signature with WebCrypto before any record is trusted; a missing,
foreign, or tampered signature halts the cockpit. The private key lives outside
the repo at `~/.config/xoras/cockpit_bundle_signing/` and is never shipped.

This proves authorship by the holder of that key, not external trust: the pin
is generated in the same build.

Three further controls are enforced in the build path:

- `dist/known_good_sources.json` is a signed manifest of 17 critical source
  files. The exporter refuses to run if any of them drifted (ghost-intrusion
  defence). Regenerate it only with `tools/known_good_sources.py --emit` after
  an reviewed source change.
- A monotonic `build_seq` is kept outside the repo at
  `~/.config/xoras/cockpit_build_seq.json` and pinned into the trust root. A
  replayed bundle with a stale sequence fails closed with `BUILD_SEQ_MISMATCH`.
- Records carry a DART clearance and the bundle declares an egress clearance;
  credential-shaped claim values are redacted at export, and a record above
  the egress level fails closed with `EGRESS_CLEARANCE_VIOLATION`.
- The exporter runs `PRAGMA integrity_check` and verifies lineage parent
  linkage before shipping, emitting a `LINEAGE_VERIFIED` required-slot record.

Consequently the bundle digest changes each build by design (monotonic build
identity), not because of nondeterministic hashing. See `SECURITY_MODEL.md`
for the remaining P0 item (DB lineage verification inside the exporter).

## Gate wiring

`reality_gate.sh` now runs nine top-level gates: production, side-channel, DART
cage lattice, Z3 containment, sovereign writer, verification-only cockpit,
CI surface (WASM + doc-sync), golden groundedness, and the lineage witness. The
current receipt reports 8/9 with the golden gate as the sole failure; production
remains 6/6. The cockpit gate never regenerates dist
assets. The root cause of the previous red gate — a poisoned
`memory/tri_brain/merkle_root.hash` — was repaired, the poisoned bytes were
preserved under `memory/intelligence/`, and the BBQ gauntlet now restores from
`memory/tri_brain/merkle_root.known_good` (0444) rather than from whatever was
on disk.

## Toolchain

Node.js 20 or newer is required (`node --test` and `--experimental-test-coverage`).
Python 3 and SQLite are required for the exporter and RAW gate. The exporter
records `git rev-parse HEAD` as provenance; if git is unavailable it records
`"unknown"` and continues. `SOURCE_DATE_EPOCH` overrides the writer receipt
timestamp for reproducible builds.

## Verification

```bash
node --test tests/*.test.mjs
```

Coverage floor (GQS-022): ≥80% line coverage is required on the canonical
modules and is enforced by `build.sh` (the build exits non-zero below the floor).
Current measured coverage: 96.60% lines, 80.95% branches, 100% functions. The suite includes NIST SHA-256 vectors, a 1,000,000-byte vector, illegal
state transitions, missing/tampered evidence, manifest tampering, an injected
`FAIL` verdict, static zero-tolerance scans (no fake hash, no `passed: true`,
no `onclick`, no `innerHTML`, no external URL), and a direct check that the
real bundle reports the real `REALITY_GATE_FAIL`.
