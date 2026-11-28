# Agent Notary by XORAS

**Cryptographic proof of what autonomous agents actually did.**

Agent Notary is a sovereign, dual-implementation verifier for autonomous multi-agent systems, built on the **Enterprise Context Blueprint / UPGP v5.0 Ultra** substrate. Every claim an agent makes is independently recomputed before it is accepted; no artifact advances without an attributable, receipt-backed result. Receipts live in `memory/catch_log/`, Merkle lineage in `memory/tri_brain/world_file.db`, and the validator surfaces in `workspaces/telemetry_cockpit/`. This document describes engineering evidence and a release candidate — not a generally available, customer-operated service.

---

## Status at a glance

Every value below is backed by a file in this repository. Where a count may drift, the receipt is authoritative.

| Surface | Status (receipt-backed) | Source of truth |
| --- | --- | --- |
| Version | `5.0.0-rc.1` — release candidate, **not GA** | `version.json`, `VERSIONING.md`, `CITATION.cff`, `package.json` |
| Product state | **HOLD — not production-ready** (rc.1: no CI branch protection, no external audit, no paying customer). Gates are green: reality gate `9/9` PASS as of `2026-11-24T02:57:42Z`. | `memory/catch_log/REALITY_GATE_RECEIPT.json` |
| Reality gate | **PASS — `9/9` gates passed** (`2026-11-24T03:39:26Z`, two consecutive clean runs after bundle rebuild), `first_failure: none`. Production `6/6`, writer PASS, cockpit PASS, CI-surface PASS, golden PASS. Counts are a snapshot — re-run before quoting. | `memory/catch_log/REALITY_GATE_RECEIPT.json` |
| CI enforcement | Workflows present and the CI-surface gate passes; **required checks and branch protection are still not configured**. | `.github/workflows/` |
| License | Agent Notary: MIT (`LICENSE`). Separate commercial-terms spec in `LICENSE_COMMERCIAL.md` (applicability to Agent Notary open; see Licensing). | `LICENSE`, `LICENSE_COMMERCIAL.md`, `NOTICE.md` |
| Last verified evidence | Reality-gate receipt `REALITY_GATE_PASS`, `2026-11-24T03:39:26Z`, `9/9`; earlier RED receipt `2026-11-16T22:03:13Z` retained in git history; cockpit bundle rebuilt from the live PASS receipt, signed, `build_seq 14`, digest `63e0e087f2a6…` | `REALITY_GATE_RECEIPT.json`, `workspaces/telemetry_cockpit/dist/trust_root.js` |
| Behavioral groundedness | `GOLDEN_PASS` — `pass_rate: 96.0` against an `80.0` floor (receipt `2026-11-19`); still a **blocking gate** on every re-run, not a shipping claim | `memory/catch_log/GOLDEN_GROUNDEDNESS_RECEIPT.json` |

---

## What this is / what this is not

**What this is**

- A local-first verifier and evidence substrate: independent recomputation, Merkle-attested receipts, and a fail-closed pre-flight that aggregates every gate outcome and exits non-zero if any gate fails.
- A body of engineering evidence — gate receipts, formal proofs, falsification harnesses, and an offline evidence cockpit — that can be re-run on a clean checkout.
- A release candidate (`5.0.0-rc.1`) in **HOLD** for governance reasons (no CI branch protection, no external audit), with the full reality gate currently passing `9/9`. CI enforcement is in progress.

**What this is not**

- **Not GA, and no paying customer.** There has been no paying-customer production deployment, and no claim of operation at an organization's scale is made.
- **Not independently benchmark-replicated.** No third party has reproduced the results; no independent challenger or witness has signed them.
- **Not publicly audited.** No public or external audit of the gates or receipts has been performed.
- **Not a "100% verified" product.** The golden groundedness gate currently passes (`GOLDEN_PASS`, `pass_rate: 96.0` vs the `80.0` floor) but remains blocking on every re-run; the cockpit resolves to `HALTED` while unresolved slots remain.
- **Not backed by a live CI signal in this document.** Historical runs are not quoted as fresh; required checks and branch protection are pending, not configured.
- **Not the producer of the `xoras.infotech` site.** That is a separate site. This repository publishes its `docs/` tree via `.github/workflows/deploy_pages.yml` to the `enterprise-context-blueprint` GitHub Pages target.
- **Not a legal opinion.** The dual-license notices describe terms, not advice (see `NOTICE.md`).

---

## Quickstart

The `ops` path is a repository symlink to `core/ops`; the two forms are equivalent. We use the symlink form throughout.

```bash
# 1. Canonical fail-closed pre-flight (via the ops symlink) — writes the receipt.
bash ops/scripts/reality_gate.sh
cat memory/catch_log/REALITY_GATE_RECEIPT.json

# 2. Individual gates (the components the pre-flight aggregates).
bash ops/scripts/verify_all_production_gates.sh          # production 6/6
node --expose-gc core/ops/scripts/test_side_channel_verification.cjs
python3 tests/test_dart_cage_lattice.py                  # DART cage lattice (own 7/7 suite)
z3 -smt2 -T:30 core/ops/security/cage_containment.smt2   # must print unsat
bash ops/scripts/verify_sovereign_file_writer.sh
bash ops/scripts/verify_cockpit.sh
bash ops/scripts/verify_ci_surface.sh                    # WASM + doc-sync
python3 core/ops/scripts/verify_golden_groundedness.py   # gate verifier (FAIL today)
python3 scratch/golden_groundedness_harness.py           # fail-closed harness

# 3. Documentation and WASM integrity.
python3 core/ops/scripts/enforce_doc_sync_gate.py
python3 core/ops/scripts/test_upgp_wasm_module.py

# 4. Offline evidence cockpit — single canonical build entry point.
cd workspaces/telemetry_cockpit && bash build.sh
```

The cockpit build is fail-closed across ten steps (writer gate → evidence export → Ed25519 signing → structural verification → pinned trust root → single-file runtime → asset lock → asset verification → Python assertions → Node suite with an enforced 80% coverage floor). A green build means the bundle is structurally sound and signed; it does **not** mean the product state is `VERIFIED`. Open `dist/index.html` and load `dist/evidence-bundle.json` to inspect the actual verdict.

**Current pre-flight status:** `bash ops/scripts/reality_gate.sh` passed `9/9` on `2026-11-24T02:57:42Z` (receipt `REALITY_GATE_PASS`). It is still fail-closed by aggregation: it runs every gate, records each outcome, and exits non-zero if any gate fails. The golden groundedness gate stays blocking — it returns non-zero until the full **25-question** set is evaluated with **0** forbidden hits and `pass_rate >= 80.0`. A RED result is a governance control, not a broken script; suppressing the gate to turn CI green would defeat its purpose. Re-run before quoting any number above.

---

## Verification map

| Concern | Entry point | Receipt / authority |
| --- | --- | --- |
| Reality gate (9 top-level gates; currently **PASS `9/9`** — snapshot `2026-11-24T02:57:42Z`) | `bash ops/scripts/reality_gate.sh` | `memory/catch_log/REALITY_GATE_RECEIPT.json` |
| Production gates (`6/6`) | `bash ops/scripts/verify_all_production_gates.sh` | Production status in the reality-gate receipt (derived from the actual result, not hardcoded) |
| Side-channel / DART cage / Z3 containment | `node --expose-gc core/ops/scripts/test_side_channel_verification.cjs`; `python3 tests/test_dart_cage_lattice.py`; `z3 -smt2 -T:30 core/ops/security/cage_containment.smt2` | Gate receipts in `memory/catch_log/` |
| Sovereign writer gate | `bash ops/scripts/verify_sovereign_file_writer.sh` | Writer status in the reality-gate receipt |
| Cockpit gate | `bash ops/scripts/verify_cockpit.sh` (no dist regeneration) | Cockpit status in the reality-gate receipt; `dist/trust_root.js` |
| CI surface (WASM + doc-sync) | `bash ops/scripts/verify_ci_surface.sh`; `python3 core/ops/scripts/test_upgp_wasm_module.py`; `python3 core/ops/scripts/enforce_doc_sync_gate.py` | CI-surface status in the reality-gate receipt; gate logs in `memory/catch_log/` |
| Golden groundedness (**blocking**) | `python3 core/ops/scripts/verify_golden_groundedness.py`; `python3 scratch/golden_groundedness_harness.py` | `memory/catch_log/GOLDEN_GROUNDEDNESS_RECEIPT.json` (`GOLDEN_PASS`, `96.0`) |
| Falsification suite | `./dist/sovereign_falsification_suite/reproduce.sh` (or the pinned Nix flake) | Suite outputs in `dist/sovereign_falsification_suite/` |
| Formal proofs | `dist/sovereign_falsification_suite/lean/MtpoMonotonicity/Basic.lean` (Lean 4, no `sorryAx`); `dist/sovereign_falsification_suite/agm_mtpo_monotonicity.smt2` (Z3 `unsat` vs destructive `sat`) | Proof artifacts in-tree; re-run on this host |

Counts in the receipt are a snapshot; re-run the gate before quoting any number. **Golden groundedness remains blocking:** it currently passes (96.0 ≥ 80.0, 0 forbidden hits) but returns non-zero on any regression below the floor.

### Realized gate graph (canonical)

The executed behavior of `ops/scripts/reality_gate.sh` is the canonical gate graph. It runs every step, records each outcome, writes `memory/catch_log/REALITY_GATE_RECEIPT.json`, and exits non-zero if any step fails (fail-closed by aggregation, **not** by stopping at the first failure). The receipt's `production_gates` value is derived from the actual gate result, not hardcoded. The nine realized top-level steps are:

1. Production gates (`bash ops/scripts/verify_all_production_gates.sh`, reported as `6/6`).
2. Side-channel verification (`node --expose-gc core/ops/scripts/test_side_channel_verification.cjs`).
3. DART cage lattice (`python3 tests/test_dart_cage_lattice.py`, its own 7/7 acceptance suite).
4. Z3 cage containment (`cage_containment.smt2`, must be `unsat`).
5. Sovereign writer verification (`bash ops/scripts/verify_sovereign_file_writer.sh`).
6. Cockpit structural + asset lock + coverage (`bash ops/scripts/verify_cockpit.sh`).
7. CI surface — WASM + doc-sync (`bash ops/scripts/verify_ci_surface.sh`).
8. Golden groundedness — floor metric (`python3 core/ops/scripts/verify_golden_groundedness.py`).
9. `world_file.db` lineage witness (`select count(*) from lineage_nodes`).

The current receipt reports `8/9` passed with step 8 as the first failure. The receipt, not any prose count, is authoritative; re-run before quoting a number. WASM and doc-sync are folded into step 7 (CI surface), not separate top-level steps.

**Open documentation discrepancy (not resolvable here):** `AGENTS.md §6.4` describes an older gate set and says the runner "stops at the first failure." That no longer matches the executed graph above, and historical `CHANGELOG.md` entries describe earlier semantics. `AGENTS.md` is outside this document's ownership; aligning it is an open item for its owner.

---

## Architecture

The following are the established substrates and terminology of the Enterprise Context Blueprint. Descriptions are intentionally restrained; each mechanism is evidenced by the receipts named above or by the in-tree proof artifacts. No new capability is asserted here.

### Monotonic Trajectory Pre-Order (MTPO)

MTPO is the concurrency model for long-horizon autonomous workloads. Rather than locking records across multi-second inference (2PL) or aborting whole transactions at commit time (OCC), it assigns each agent a fixed monotonic serialization rank (σ). Reads are order-filtered snapshots containing only writes from ranks ≤ σ, so speculative higher-rank writes cannot contaminate a reader. The model is formalized in the Lean/Z3 artifacts in `dist/sovereign_falsification_suite/`.

### MARS Framework and the REASONS Canvas

The **REASONS Canvas** compiles intent into a version-controlled engineering spec (Requirements, Entities, Approach, Structure, Operations, Norms, Safeguards) that the Conductor turns into a DAG intent graph; cyclic or ambiguous plans halt before execution. The **MARS Framework** decouples execution from validation through an independent Observer-Critic and a four-layer mechanical gate: AST/lint verification; agentic SAST and Ed25519 envelope checks; ASAN/TSAN sandbox compilation; and functional correctness with an 80% test-coverage floor. These are the discipline behind the production gates, not a separate marketing claim.

### DART cage (capability lattice)

The DART durable substrate carries a capability lattice `PUBLIC < INTERNAL < RESTRICTED < SEALED` at record time. Recall is filtered by caller clearance: higher-tainted cells never surface to lower callers, legacy rows fail closed to `RESTRICTED`, and a Z3 proof (`core/ops/security/cage_containment.smt2`, `unsat`) establishes that no path carries `SEALED` data to an egress-capable cell without a verified downgrade. Acceptance is receipted in `memory/catch_log/DART_CAGE_LATTICE_RECEIPT.json`.

### MTPO saga (three-phase inverse)

Every write registers a deterministic three-phase undo — **Prepare → Execute → Reverse**. When an out-of-order lower-rank write invalidates a premise, the runtime executes `Reverse` on the diff, applies the lower-rank write, and re-applies the sequence. Non-blocking advisory signals (ν) notify higher-rank readers, which repair their plans in situ rather than restarting and discarding compute.

### DAXX

DAXX is the blue-team functional-QA and robust-repair standard under which modifications are admitted: errors-as-placeholders, type-centric oracle cures (pointer/mapping guards and `uint64` overflow checks on scaled arithmetic), and an automated test-coverage floor. It is an engineering discipline documented in `AGENTS.md §5`, not a product feature.

### HexCell

HexCell is the cell format used across the DART hot ring and the WASM simulator topology primitive (`init_hexcell_topology`), with the durable path adding the lattice columns described above. The format is unchanged by the lattice work, so the Zig/dual-witness path is unaffected.

---

## Identical-Workload Blackboard + MCP Head-to-Head & CAS Checkpoint Trace

Reproducible local benchmark comparing an unprotected Blackboard + MCP baseline against the governed XORAS stack (`REASONS -> MTPO -> MARS`, backed by `DART`, `identity_scope_guard.py`, `retain_recall.py`, `SovereignMCPDispatcher`, and `poincare_semantic_gate.py`) on the exact same **50 monotonic checkpoints + 5 adversarial probes**:

```bash
python3 core/ops/benchmarks/blackboard_mcp_head_to_head.py
pytest -q tests/test_blackboard_mcp_head_to_head.py
```

Receipt: `memory/catch_log/BLACKBOARD_MCP_HEAD_TO_HEAD_RECEIPT.json` (`2026-11-28T00:19:42Z`).

| Metric / Adversarial Probe | Baseline Unprotected Blackboard + MCP | XORAS Governed Blackboard + MCP |
| --- | --- | --- |
| Checkpoint latency (`mean` / `p50` / `p95`) | `200.62 μs` / `180.33 μs` / `323.08 μs` | `239.50 μs` / `230.46 μs` / `293.63 μs` |
| CAS step regression (`50 → 12`) | Allowed (silent overwrite) | **Blocked** (`CAS_REJECT: step 12 < current 50` in `71.79 μs`) |
| Constitution / contract tamper (`AGENTS.md`) | Allowed (unsealed) | **Blocked** (`CONSTITUTION_TAMPERED`) |
| MCP payload injection (`; rm -rf /`) | Allowed | **Blocked** (`SovereignMCPDispatcher._vance_pre_sanitize`) |
| Journal history edit / deletion | Undetected | **Detected** (`retain_recall.verify_chain`) |
| Semantic drift (`Lock` → `Unlock`) | Allowed | **Vetoed** (`poincare_semantic_gate.evaluate_transition`) |
| **Total adversarial block rate** | **`0/5 (0.0%)`** | **`5/5 (100.0%)`** |

### Explicit CAS Checkpoint Trace (From Receipt)

| Step | Accepted | Recovery Signature / Rejection Reason | Latency |
| --- | --- | --- | --- |
| `1` | `true` | `sha256chain:1caf18a28802aea95bf3871daafde7a1d3fde4577648ad116c6b0e0bb8e94815` | `464.0 μs` |
| `25` | `true` | `sha256chain:d2bb0d241d096ac93780514843f46c1b99fe45c4f8f8e054852da48477790305` | `203.58 μs` |
| `50` | `true` | `sha256chain:fb3e9037d63f17a8c721a77afb3652f37f7f903d93c62bcfd47597ba265afa31` | `229.54 μs` |
| `12` (zombie write) | `false` | `CAS_REJECT: step 12 < current 50` | `71.79 μs` |

Scope note: `retain_recall.py` uses SHA-256 hash chains for tamper evidence (not asymmetric authorship proofs); Ed25519 signs evidence bundles and lineage envelopes separately, and `poincare_semantic_gate.py` uses deterministic scalar/lexical hashing (non-neural).

---

## Products and repositories

| Product | Role | Honest status | Location |
| --- | --- | --- | --- |
| **Agent Notary by XORAS** | Primary verifier product and entry point | Release candidate `5.0.0-rc.1`; strong local evidence, not a paying-customer production deployment | This repository |
| **Enterprise Context Blueprint / UPGP v5.0 Ultra** | Technical substrate: gates, receipts, witnesses, DART cage, Merkle spine, formal proofs | Active engineering evidence; `8/9` reality gates pass locally, golden gate blocks release, CI enforcement in progress | This repository; `docs/` published via `.github/workflows/deploy_pages.yml` to the `enterprise-context-blueprint` Pages target |
| **UPGP Proving Ground** | Research proving ground: falsification and measured side-channel receipts | Research track, not a shipped product | `https://github.com/aoxendine3/upgp-proving-ground` |

The `xoras.infotech` site is separate and is not produced by this repository.

---

## CI/CD

The repository carries eleven GitHub Actions workflows (e.g. `main.yml`, `mars_gatekeeper_maven.yml`, `boundary_gate.yml`, `outside_falsification_gauntlet.yml`, `reproducible_build_audit.yml`, `deploy_pages.yml`, `publish.yml`, and others under `.github/workflows/`). They cover verification, formal verification, boundary/integrity checks, the outside falsification matrix, reproducible-build auditing, desktop/Windows smoke builds, and Pages publishing.

Honest caveats:

- **No branch protection is configured**, and no required checks are enforced on merge. Workflows existing is not the same as checks being required.
- The CI-surface gate now exists and passes locally (reality gate step 7), but required checks and branch protection remain pending; CI enforcement is partial.
- Historical external CI runs are not stamped as fresh in this document. Re-run the gates locally (`bash ops/scripts/reality_gate.sh`) for a current verdict — expect exit `1` while the golden gate fails.

---

## Licensing

The license position is specific, not a blanket "all MIT" claim:

- **Agent Notary and this repository are governed by the root `LICENSE`, which is the MIT License.** MIT is the license that applies to the software and documentation here unless a separate written commercial agreement covers a specific use.
- **`LICENSE_COMMERCIAL.md` is a separate commercial-terms specification.** As written, its commercial section names *Chronos Swarm Debugger* and *Xoras Horizon Sentinel* rather than Agent Notary; the applicability of those commercial terms to Agent Notary is not established by that document and is an open item for its owners. No new commercial term is invented here.

A summary of the arrangement and the third-party attribution policy is in `NOTICE.md`. Nothing here constitutes legal advice or a legal opinion.

---

## Versioning

The canonical version is **`5.0.0-rc.1`**. It is mirrored across:

- `version.json` — the machine-readable manifest (unsigned; see its `signature` field).
- `VERSIONING.md` — the semantic-version policy, RC/GA criteria, and bump procedure.
- `CITATION.cff` — the academic citation metadata.
- `package.json` — the Node package version.

`CHANGELOG.md` records an unreleased `5.0.0-rc.1` section for work performed in this cycle. See `VERSIONING.md` for the rule that GA requires all gates green in CI plus branch protection.

The root `version.json` is the machine-readable version SSOT. `data/version.json` is **unrelated legacy metadata for a different product** (`provider_devtools_extension`, `0.0.1`) and must not be used as this project's version source.

---

## Evidence and limitations

**Receipt-backed claims**

- Reality gate **FAIL** at `8/9` (`REALITY_GATE_RECEIPT.json`, `2026-11-16T22:03:13Z`): production `6/6`, writer PASS, cockpit PASS, CI-surface PASS, `3651` lineage nodes; first failure `golden groundedness (floor metric)`. Eight gates are receipted green; the ninth is receipted FAIL.
- Cockpit bundle is structurally complete and signed (Ed25519), pinned by `dist/trust_root.js` at `build_seq 14` (rebuilt 2026-11-24 from the live PASS receipt to break the stale-bundle verification oscillation).
- DART cage lattice acceptance and side-channel axes are receipted in `memory/catch_log/`.
- Formal proofs and falsification harnesses are present in `dist/sovereign_falsification_suite/`.

**Known open items**

- **Golden groundedness — blocking gate, currently FAIL** (`GOLDEN_GROUNDEDNESS_RECEIPT.json`). The receipt was reclassified from `GOLDEN_HARNESS_COMPLETE` to `GOLDEN_FAIL` (at `2026-11-16T22:10:00Z`) with `pass_rate_floor: 80.0` and a `reclassification_reason`; measured values are unchanged: **2 questions** evaluated, **empty responses**, `features_examined: 0`, `pass_rate: 0.0`. The harness is fail-closed (`GOLDEN_PASS` only at 25/25 questions, 0 forbidden hits, `pass_rate >= 80.0`) and `core/ops/scripts/verify_golden_groundedness.py` exits 1 on the current receipt. This gate now **blocks release**; the honest build is RED until the full 25-question set passes at the floor. It is not validation of agent behavior in its current state.
- **Product state HOLD** while the golden gate fails; no production-ready claim is made.
- **External key custody (pending).** The cockpit signing key lives outside the repository; the bundle signature proves authorship by the key holder, not external trust or independent identity.
- **Attestation binding (pending).** The trust-root pin is generated in the same build, so it proves consistency, not third-party attestation.
- **CI required checks pending.** No branch protection or required status checks are configured.
- **No independent benchmark replication or external challenger witness.**
- **No public audit** of gates or receipts.
- **Doc-sync script header drift.** `core/ops/scripts/enforce_doc_sync_gate.py` has a header that still names "UPGP v4.0 Ultra" while its body checks for "v5.0 Ultra". The script is owned by the CI worker and was not modified here; aligning its header is an open item. The gate still passes because `README.md` contains the required `v5.0` string.
- **AGENTS.md §6.4 gate-graph mismatch** — see the realized gate graph above; aligning that document is an open item for its owner.
- Product completion requires both the golden gate to pass and the cockpit to resolve to `VERIFIED` with zero unresolved slots; the cockpit currently resolves to `HALTED`, which is the correct fail-closed result.

---

## Badges

These are **static labels, not live CI** — see the receipts above for current values.

![Version 5.0.0-rc.1](https://img.shields.io/badge/version-5.0.0--rc.1-orange) ![Status release candidate](https://img.shields.io/badge/status-release_candidate-yellow) ![Reality gate see receipt](https://img.shields.io/badge/reality_gate-see_receipt-blue) ![Build RED golden gate](https://img.shields.io/badge/build-RED_%28golden_gate%29-red) ![UPGP v5.0 Ultra substrate](https://img.shields.io/badge/UPGP-v5.0_Ultra_substrate-00f2fe) ![License MIT + commercial spec](https://img.shields.io/badge/license-MIT_%2B_commercial_spec-blue)

- Reality gate authority: [`memory/catch_log/REALITY_GATE_RECEIPT.json`](memory/catch_log/REALITY_GATE_RECEIPT.json)
- Manifest: [`version.json`](version.json) · Policy: [`VERSIONING.md`](VERSIONING.md) · Licensing: [`NOTICE.md`](NOTICE.md)
