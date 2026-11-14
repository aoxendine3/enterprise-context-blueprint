# COGNEN / SSOT Synthesis — Verified Audit (2026-11-14)

> **Provenance & verdict (added 2026-11-14 by the collective; body not reproduced verbatim — see chat).**
> This document audits a user-pasted synthesis that fuses Atlan/Fin marketing, a garbled CogNGen mathematical sketch, and XORAS::OS terminology into one "verified" claim. It is **not** verified, is **not** for citation, and must not be shown externally. Filed under documentation law with this audit as its provenance header.

## Verdict: COMPROMISED — VENDOR MARKETING + MISSTATED CITATION + THEATRICAL CODE CLAIM

### Section 1 — Atlan hallucination metrics
Claims lifted from atlan.com's own pages: "+38% SQL accuracy (174 queries)", "9% → 81% media company", "40%+ hallucination reduction", "5 structural metrics".
- **Verified as vendor-published** (atlan.com, updated June 2026), not independently replicated by us or third parties; the "40%+" figure traces to "MEGA-RAG" (PMC) / graph retrieval research — real peer-review track, still benchmark-bound.
- The "9% → 81%" is Atlan's own anonymized media-customer anecdote. Not a controlled result.
- **Classification: VENDOR-CLAIM, cited-but-unverified.** Legitimate to reference as a market signal with attribution; not legitimate as "Atlan achieves this, therefore we do too."

### Section 2 — Fin (Intercom) <1% / 76% / 12,000+
Verified on fin.ai and intercom.com/help: <1% hallucination FAQ claim; 76% resolution across "12,000+ customers"; 2M weekly resolutions; $0.99/outcome; Salesforce acquisition announced ~$3.6B (June 2026, closing pending).
- **Classification: VENDOR-CLAIM.** Third-party independent measurements report 38–73% spread (helpin review, Sept 2026). No independent audit of the <1% figure exists.
- Porting Fin's marketing as architectural guidance is not engineering and not allowed under our branding law (third-party product branding presented as fact).

### Section 3 — CogNGen mathematics
Against the paper (arXiv:2310.15177):
- Document writes `e^ℓ(t) = z^ℓ(t) − W^{ℓ+1}(t) · φ(z^{ℓ+1}(t))` — **missing the 1/Σ_ℓ precision factor and the z̄_ℓ mean structure**; error neuron definition is wrong.
- `∂F/∂z^ℓ = e^ℓ(t) − E^ℓ(t)ᵀ e^{ℓ−1}(t)` — sign/order garbled vs paper Eq. (4).
- "Hebbian sleep-cycle replay" presented here as `dW = 0.01·outer(z_t, error)` — a generic outer-product update, not the published Eqs. (5–6) (τ_w, τ_e timescales, weight decay γ_w/γ_e, correct term orientation), and emphatically not NGC as implemented in CogNGen.
- The document omits the paper's key mathematics entirely (clamping, mean-field assumption, joint distribution, b=100 MINERVA 2, Hopfield 3-way evolution with equations 10–12).
- **Classification: MISSTATED — do not cite as CogNGen.**

### Section 4 — "Verified bare-metal implementation" code block
Ran verbatim on this host (`/tmp/cogngen_kernel_audit.py`):
```
db_path: /core/.agents/world_file.db   ← absolute path that does not exist; never opened
vfe: 344.87 (random 768-dim vectors, W_g random ×0.01)
W_g changed by training-like update: True   ← 2 outer-product updates on random tensors
```
- A NumPy toy with **zero** integration: no DART, no MARS gate, no world_file.db, no Notary, no DART lattice, no MTPO, no witness.
- "Ready to deploy inside /workspace/scratch/cogngen_kernel.py" — the doc itself admits it belongs in scratch; it is not a "bare-metal Active Inference Kernel" and not "verified".
- **Classification: THEATRICAL — illustrates API shape only.**

### Section 5 — XORAS::OS section re-mixing real parts with invented ones
- Real: world_file.db, HexCell 3,200B (matches `init_hexcell_topology(25)=3200` in the WASM), MTPO Σ ordering, MARS gate existence, Reality-as-SSOT concept, dual-witness.
- Invented/misstated: **TCP 8787** (no kernel socket; 11434 is Ollama and is UDP — mislabeled as kernel socket too), "ane/SIMD-mapped Repr(C, align(128))" (no such code in the stack), **MARS Four-Layer Gate as `cargo fmt / Ed25519 / ASAN-TSAN / ≥80% coverage`** (our actual MARS: AST · agentic SAST · ASAN/TSAN · Z3 SMT; the coverage claim "≥80% with FAIL-to-PASS metric" exists nowhere in our gate suite).
- **Classification: PARTIALLY REAL, MISLABELLED, EXAGGERATED.**

### Required corrections before any reuse
1. Strip or properly attribute Atlan and Fin references (branding law; vendor-claim flags).
2. Replace Section 3 math with arXiv:2310.15177 verbatim (or cite arXiv:2204.00619 / AAAI-SS 27702 directly).
3. Delete or clearly label the code block as a *non-functional illustrative sketch*; it never touches our verified substrates.
4. Correct MARS description to AST · SAST · ASAN/TSAN · Z3 (our 6/6 gates, not "coverage ≥80%").
5. Remove invented ports/interfaces (TCP 8787) or back them with real sockets.

## Fitness for XORAS
Useful ONLY as a market/competitive signal ("the whole enterprise market is converging on exactly the problems our verified stack solves"). The technical content is unusable as engineering reference. File it as a market note, never as an architecture doc.
