# CS2023+ DELTA CURRICULUM SPECIFICATION

**Status:** Specification (source of truth for the CS2023+ Delta video cuts and
chapter 1 of `XORAS_Bio-Cognitive_Core.mp4`).
**Provenance:** Transcribed from the collective's own production sources —
`cs2023_video/tts_gen.py` (Kokoro narration), `cs2023_video/make_cards.py`
(card render texts) and `cs2023_video/build_videos.py` on the backup USB, plus
the Bio-Cognitive Core video frames (chapter 1: "CS2023+ Delta Arch — Syntax
to Verification"). Every number below appears verbatim in those sources;
nothing here is invented.

---

## 1. What the Delta Is

CS2023+ is a **delta, not a replacement** of the ACM/IEEE-CS/AAAI CS2023
"Sunflower" curriculum: same degree, same credit load, same 268-hour universal
core — **repriced for the era when syntax is free and verification is not**.
The shift runs from *authoring* to *assuring*, from *typing* to *proving*,
from *hoping* to *measuring*.

The opening claim of the curriculum: **AI writes code in milliseconds, but if
you cannot verify what it generated, you are not shipping software — you are
shipping liabilities.**

## 2. The Hour Reallocation (the core mechanism)

| Item | CS2023 (legacy) | CS2023+ (Delta) |
| --- | --- | --- |
| Universal core total | 268 hours | **268 hours (unchanged)** |
| Manual syntax drills (SDF — legacy) | 43 hours | 23 hours |
| AI verification & invariant auditing | 0 hours | **+10 hours** |
| Systems & memory-safety hygiene | 0 hours | **+10 hours** |
| Hours **moved** (not added) | — | **20 hours** |

Lower-third canonical phrasing: **"CS2023: 43h syntax → CS2023+: 23h + 10h
verify + 10h safety"** — total core stays 268h.

### 2.1 The two new 10-hour blocks

1. **AI verification and invariant auditing** — writing Hoare triples,
   mutating assertion bounds, auditing what the solver actually proved.
2. **Systems and memory-safety hygiene** — race conditions, pointer bounds,
   unbypassable input validation.

Learning outcome (narration, verbatim intent): *a graduate who can prove code
instead of merely run it.*

## 3. Why Formal Logic (the pedagogical spine)

One rule drives the curriculum: **when a precondition is false, axiomatic
semantics evaluates any command to any postcondition — false proves
anything.** Unverified generated code is exactly that: a false premise wearing
a working demo. It compiles, it passes a glance, and it carries a hidden race
that only detonates under production load.

Therefore: feed invariants to SMT solvers and require **machine-checked
proofs**. A human eye cannot scale to thousands of generated lines; a solver
can.

This is the same doctrine the tree already executes:
`core/ops/scripts/z3_exponentiation_vc.py` (axiomatic VC proof),
`core/ops/scripts/z3_separation_logic_vc.py` (frame rule — absence of pointer
and data races), `core/ops/security/cage_containment.smt2`.

## 4. Standards Alignment

- **ACM/IEEE-CS/AAAI CS2023** — Sunflower Curriculum (universal core, 268h).
- **IEEE SWEBOK v4** — software engineering body of knowledge alignment.
- Card text (canonical): *"Aligned: CS2023 Sunflower Curriculum + IEEE
  SWEBOK v4"*, *"ACM/IEEE-CS/AAAI CS2023 · IEEE SWEBOK v4"*.

## 5. Benchmark Claim (sandbox evidence card)

Stated with its test environment on a dedicated card (chapter-6 companion
claim of the CS2023+ videos):

- Substrate: own sandbox, **kernel-level SECCOMP-BPF filters** against a
  privilege-escalation exploit corpus.
- Result: **11 critical exploits — 11 blocked.**
- The boundary held because the kernel enforced it, not the application.

Tree corroboration for the SECCOMP posture: `core/native/upgp_wasm_core.c`,
`core/ops/security/z3_upgp_containment_oracle.py`,
`core/products/upgp/SeccompProfile.ts`.

## 6. CS2030 Lineage (provenance note)

The video cuts were built from the supplied **CS2030** source:
`build_videos.py` states *"Build two CS2023+ Delta video cuts from the
supplied CS2030 source"* and *"Title: replaced 'CS2030 AI Architecture' with
'CS2023+ Delta Architecture'"* (source file:
`CS2030_AI_Architecture.mp4`, not present in the tree or on the USB). The
CS2023+ Delta *numbers* in this document come entirely from the CS2023+
narration/card sources above — no CS2030-specific figures are asserted here
because no CS2030 source text survives to verify them against.

## 7. Card Index (video render inventory)

Cards rendered by `make_cards.py` (USB `cs2023_video/cards/`): `benchmark`,
`formal`, `hours`, `legacy_matrix`, `lt_bench`, `lt_hours`, `lt_proof`,
`lt_swebok`, `outro`, `petal`, plus chapter cards. Canonical lower-thirds:
`lt_hours` (hour reallocation), `lt_swebok` (standards alignment),
`lt_proof` (proof framing), `lt_bench` (SECCOMP-BPF 11/11).
