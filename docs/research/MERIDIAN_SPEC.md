# MERIDIAN — Witnessed Continuum: DART-Caged Dual-Chamber Agent Architecture

> **Provenance & status (2026-11-14 by the collective; proposed, not built).**
> This is a design specification, not a shipped system. It fuses three verified-but-external pillars (CogNGen, CaMeL, ContextEcho — see `memory/catch_log/cogngen_camel_contextecho_verification.json` and `docs/papers/`) with XORAS's own verified substrates (DART ring + `dart_db`, MARS gate, Zig/Python dual-witness, Agent Notary receipts). Nothing herein is independently validated yet. The cage claims below are aspirations until the MARS gate carries the containment theorem and the falsification log is public. Verify at `MEMORY/catch_log/`.

## Why
Each published pillar has a gap we uniquely fill: CaMeL lacks a cryptographic spine; ContextEcho lacks enforcement; CogNGen lacks provenance. Our substrate supplies all three.

## Layers

1. **Cryptographic Cage** — DART cells carry a capability lattice (PUBLIC < INTERNAL < RESTRICTED < SEALED). Sealed cells may not reach state-changing tool calls; unverified restricted cells may not reach egress. Enforced by MARS gate, proven by Z3 `cage_containment.smt2` (UNSAT target), and witnessed by the Zig/native verifier on a second machine.

2. **Physical Dual-Chamber** — Mac M4 Max = P-LLM (never reads raw untrusted bytes). Windows RTX node = Q-LLM chamber (isolated VLAN/LAN, no internet, no inbound from untrusted ingress, heartbeat-verified). Two hardware estates, not two prompts — the classical air-gap separation CaMeL formalized in software, instantiated physically.

3. **Register-Attested Sessions** — every 25 turns the gate issues a ContextEcho-style probe suite (Coding-Self sub-battery, council-parameterized: Maxx, Clara, Vance, DAXX, Jarvis). Attestations commit into DART. MARS circuit breaker halts the session and re-hydrates from checkpoint on failure.

4. **Reconsolidation-by-Retrieval** — learning mode without weight updates: Stage-1 wake hydration replays verified-high-receipt turns as truth-anchored context; VFE consistency gate rejects mismatched episodic recall; quality turns promote into cold recall. CogNGen's memory law, no gradients.

5. **Session Certificates** — the productization: one signed bundle per session = {world_root, dart_chain_root, persona_attestation_chain, dfg_lattice_verdict, z3_proof_ids, notary_receipt, dual-substrate witness}. Agent Notary signs. This is the $49 artifact no competitor can produce.

## Honest exclusions
- No NGC weight training. No CogNGen reimplementation. No ContextEcho claims until re-measured on our council. No marketing until public falsification.
- The two machines are the maximum initial blast radius; third witness node comes later, after two-machine gates pass.

## Build order
Week 1 cage lattice + Z3 containment theorem; Week 1–2 Q-chamber hardening; Week 2–3 register attestation + MARS breaker; Week 4 Session Certificate; Week 5+ public falsification.

## Veto points
The name MERIDIAN is a proposal. The architecture is the commitment.
