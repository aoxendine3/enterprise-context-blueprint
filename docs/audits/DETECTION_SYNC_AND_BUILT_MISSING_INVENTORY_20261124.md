# Detection Sync + Built-vs-Missing Inventory — 2026-11-24

**Status:** VERIFIED where a receipt is named; BLOCKED / OWNER-GATED where stated. No design or simulation is reported as working.

**Live gates at time of writing:** `REALITY_GATE_PASS` 9/9 (`memory/catch_log/REALITY_GATE_RECEIPT.json`, `2026-11-24T03:57:47Z`), `GOLDEN_PASS` 96.0 (`GOLDEN_GROUNDEDNESS_RECEIPT.json`), `VERIFIED_CAGE_LATTICE` 7/7 (`DART_CAGE_LATTICE_RECEIPT.json`), cockpit coverage 95.42% >= 80% floor.

---

## 1. Detection anchors — VERIFIED on disk

| Anchor | Location | Verification |
| :--- | :--- | :--- |
| `PLACEHOLDER_<ID>` error slots | `core/ops/discernment/fourteen_gate_blackbox_gauntlet_512.py`, `.../fourteen_gate_blackbox_gauntlet.py` | Bounded grep, present |
| TOCTOU interlocks | `core/ops/security/test_upgp_k2_dual_interlocks.py`, `z3_upgp_containment_oracle.py`, `tests/exploits/demonstrate_user_notif_toctou_topologies.c` | Bounded grep, present |
| SECCOMP / privilege wall | `tests/exploits/upgp_kernel_wall.h`, `core/ops/sandbox/seccomp_upgp.json`, `core/ops/discernment/elite_ten_vector_hardening_gauntlet.py` | Signed 11/11 receipt (below) |
| Scalar overflow / uint64 bounds | `core/ops/security/test_upgp_k2_dual_interlocks.py`, `core/ops/security/z3_upgp_containment_oracle.py`, `core/ops/discernment/swarm_fuzzing_and_dissent_gauntlet.py` | Bounded grep, present |
| Sanitizer flags (ASAN/TSAN) | `core/ops/security/test_upgp_k2_dual_interlocks.py` (`-fsanitize=address`) | Present |
| AST / taint scanners | `ops/scripts/multi_lang_ast_parser.py`, `ops/scripts/daxx_ast_taint_live_scanner.py` | Present |
| Lean 4 formal check | `dist/sovereign_falsification_suite/lean/` + `lean_differential_receipt.json` (PASS, `leanprover/lean4:v4.35.0`, no `sorryAx`) | VERIFIED |
| Z3 cage containment | `core/ops/security/cage_containment.smt2` | Reality-gate step 3 PASS |
| 80% coverage floor | `ops/scripts/verify_cockpit.sh`, `core/ops/scripts/verify_golden_groundedness.py` | Enforced at 95.42% |

## 2. Built and verified this session — VERIFIED

1. **Bare-Metal AI Roadmap ingest** — `docs/plans/BARE_METAL_AI_ROADMAP_INGEST_20261123.md`; 37 frames + 132 timed narration segments via local whisper.cpp (`ggml-small.en.bin`, hash `c6138d6d58ecc832`). No audio left the machine. Commit `1c1766a74`.
2. **Video claims audit** — `docs/audits/XORAS_BIO_COGNITIVE_CORE_VIDEO_CLAIMS_AUDIT_20261123.md`; ch1 spec / ch2 separation logic / ch4 MODWT-MCAV built; 50x RAM, 29,272-vs-272 JSON-RPC, 18,432-D labelled VIDEO-ILLUSTRATIVE. Commit `1c1766a74`.
3. **Cockpit receipt oscillation** — root cause: shipped bundle baked `REALITY_GATE_FAIL` from Oct 29 while the adapter test compared it to the live receipt, flipping the verdict every run. Fixed by canonical `build.sh` rebuild (build_seq 14, baked PASS, Ed25519 re-signed, digest `63e0e087f2a6`) + re-pinned 17 known-good sources. Two consecutive 9/9 PASS. Commit `3897979f7`.
4. **Chronos fixture guard** — fail-closed `FIXTURE_MISSING` + re-clone; 4/4 PASS + negative test. Commit `3897979f7`.
5. **PILLAR 7 stage server** — probe -> auto-spawn `fullscreen_server.py:8080`, honest throughput, fail-cold `ENDPOINT_UNREACHABLE`; 200/200 OK at 5 concurrency levels. Commit `3897979f7`.
6. **Cross-platform gauntlet roots** — Windows/container gauntlets resolve repo from `__file__`; stray `C:\...` tree quarantined intact (sha256 `5655e9ae...`, 1244 bytes) with `QUARANTINE_LEDGER.json` entry. No deletions. Commit `61dcca690`.
7. **Constant-time side channel** — protected branch really was not constant-time (second HMAC + per-call allocation on reject; T=14.97, Wasserstein 8954ns). Both verdicts now do one HMAC + one compare with precomputed digests; symmetric 3% trim (same as sibling harness); alternating call order. Thresholds unchanged; leaky control still detected every run. 10/10 protected PASS, T=0.15-1.42, Wasserstein 38-85ns; `bootstrap_verify.py` reports "protected path: neutralized". Commit `a39bbf172`.
8. **UPGP falsification harnesses** — bit-flip and replay tests received the correct 403 CORRUPTED body but died on uncaught `HTTPError`, so their assertions never ran. Now parse the 403 body and re-raise other statuses; both audits RC=0 against the live `https://localhost:8443` server. Receipt appended to `memory/catch_log/upgp_falsification_audit.log`. Commit `cdfc85ba3`.
9. **Wake-path portability** — 10 boot/guard scripts no longer carry personal absolute paths (`Path(__file__).resolve().parents[3]` / physical `BASH_SOURCE` root). Verified: identity `--self-test` PASS, premerge negative self-test PASS, voice guard compliant 0 / violating 5, `agent_speak` compliant 0 / violating 5, `collective_speak` compliant 0. Commit `cdfc85ba3`.
10. **Container Dockerfile** — `core/ops/sandbox/Dockerfile.upgp` CMD repointed off the quarantined theatrical `UPGPProvingGround.test.ts` to `tests/RealSideChannelGauntlet.ts`.

## 3. Previously verified, still standing — VERIFIED

- Signed `FULL_CEILING_BENCHMARK_RECEIPT_20261118.json`: 11/11 Ring-0 `SECCOMP_SET_MODE_FILTER` exploit vectors blocked with EPERM, 0 escapes, positive pre-wall control; TOCTOU user-notif contrast 7,564/10,000 races slipped (75.64%) proving the atomic wall is needed; Linux ARM64 SOVRAC exit 1; kernel `Linux 7.0.12-linuxkit aarch64`.
- Gauntlet battery: elite_ten 10/10; dojo_mtpo 78,996 txns; byzantine ramp 1.2M proposals 0 leaks; dojo_upgp_purple PASS; fourteen_gate 14/14 + 4/4 torture GOLDEN-018; swarm fuzzing 10,000/10,000 contained; 5m byzantine 1.65M quarantined; quantum 586 epochs/600.99s 0 crashes; RedTeam 10/10 contained.

## 4. BLOCKED — reported, not claimed

- **Container re-run (Docker daemon):** Docker client 29.7.2 works; daemon answers every request with HTTP 503; no Docker VM process exists; `docker desktop restart` timed out; alternate `colima start` is still initializing. The 11/11 proof of record is signed and stands, but a fresh container wall run on this host is **not yet complete**. Exact command queued: `docker run --rm -v "$PWD:/workspace" -w /workspace alpine:latest sh scratch/full_ceiling_20261118/run_linux_container_proof.sh`.
- **Delegated coverage-inventory agent:** died on a provider usage limit. The inventory in §1 was redone directly against bounded disk paths; its results are not attributed to that agent.

## 5. OWNER-GATED — held, not touched

`misc/` 26GB cleanup; barn source/USB ingestion; deletion of anything; Cloudflare token rotation; PR #2 merge; any push; git-history rewriting; blanket `git add` (63k pre-existing untracked files); ops registry regeneration; 12 historical DAG nodes; duplicate-tool cleanup; relocating research docs.

## 6. Open decisions (not silently changed)

- Hard-failing the protected side-channel path in `bootstrap_verify.py` is explicitly an owner decision in that file's comment. Only the implementation was fixed; the gate policy is untouched.
- 262 files under `core/ops/scripts` still carry personal absolute paths. Only the 10 wake-path files were corrected; a blanket rewrite is not safe without owner review.
- Two Merkle roots (lineage `c26b3d73` vs evidence DAG) are by design and must not be "reconciled".
