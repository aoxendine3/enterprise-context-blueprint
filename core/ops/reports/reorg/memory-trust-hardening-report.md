# Memory Trust Hardening Report

**Date:** 2026-07-04  
**Scope:** P0 persona/chat memory bridge, trust labels, memory-to-prompt sanitization  
**Runtime:** `AI_Core/Xoras_Project/xoras-core/Source/`

## Summary

Persona compose no longer depends on the L2 SHM/Mongo trade-signal bridge. A dedicated persona memory bridge implements `enrich_chat` / `persist_turn` / `index_dream_insight` with trust labeling and injection sanitization. Untrusted memories cannot enter the system prompt as instructions.

## Files Changed

| File | Change |
|------|--------|
| `Source/xoras_persona_memory_bridge.py` | **New** persona/chat memory bridge (`ChatContext`, trust labels, sanitization, singleton `get_memory_bridge`) |
| `Source/xoras_persona_engine.py` | `PromptComposer` defense-in-depth sanitization; memories labeled as data-only |
| `Source/xoras_persona_api.py` | Import persona bridge (not L2) |
| `Source/xoras_langgraph_engine.py` | Import persona bridge; fail-closed PersonaDetect (no silent sovereign fallback) |
| `Source/xoras_dream_orchestrator.py` | Dream insight funnel uses persona bridge (`index_dream_insight`) |
| `Source/tests/contracts/test_memory_trust.py` | **New** trust + lock contract tests |
| `Source/tests/test_persona_engine.py` | Align explicit-override tests with lock modes |
| `ops/reports/reorg/memory-trust-hardening-report.md` | This report |

**Unchanged:** `Source/xoras_memory_bridge.py` (L2 SHM/Mongo trade-signal bridge intact).

## Trust Model

| Label | Prompt injection |
|-------|------------------|
| `trusted_system` | Allowed (sanitized) |
| `trusted_user` | Allowed (sanitized) |
| `untrusted_external` | Excluded from system prompt by default; visible in `ChatContext.memories` as `[untrusted_external] ...` |

Optional: set `XORAS_MEMORY_INCLUDE_UNTRUSTED=1` to append sanitized, labeled data-only lines (never as role/system instructions).

## Sanitization

Blocked patterns (bridge + `PromptComposer`):

- ignore/disregard/forget previous instructions
- `system prompt:`
- `you are now` / role claims (`system:`, `assistant:`, `role: system`)
- act-as-system/admin, override safety/persona

## Persona Lock Integration

`enrich_chat(..., override_source=...)` is passed through to `PersonaEngine.compose_for_chat`. Fixed mode rejects user inline switches and untrusted explicit overrides; trusted sources (`system`, `trusted`, `api`, `operator`) may override.

## Tests Run

```text
python3 -m py_compile xoras_persona_memory_bridge.py xoras_persona_engine.py \
  xoras_persona_api.py xoras_langgraph_engine.py xoras_memory_bridge.py \
  tests/contracts/test_memory_trust.py tests/test_persona_engine.py

python3 -m unittest tests.contracts.test_memory_trust tests.test_persona_engine -v
```

**Result:** 16/16 OK

Covered:

- Locked mode rejects inline persona switch
- Locked mode rejects untrusted explicit override
- Trusted override source allowed in fixed mode
- Untrusted injection text does not appear as system instructions
- Trusted user memory is injected
- PromptComposer strips imperatives

## What Works

- Persona API and LangGraph call the persona bridge contract (no AttributeError on L2).
- L2 SHM bridge remains standalone for market/signal ingestion.
- Compose failures in LangGraph fail closed (empty persona fields + error log), not silent sovereign.
- Memory trust boundary enforced before prompt composition.

## Remaining Blockers / Follow-ups

1. **Persistence is in-process only** — persona memories do not yet survive process restart; wire to vector DB / Mongo with `trust_label` metadata when ready.
2. **No contract Protocol module** — blueprint’s `xoras_memory_bridge_contract.py` / `assert_persona_bridge_contract` not added (callers use concrete persona bridge).
3. **Domain detection still active under lock** — fixed mode blocks *override* paths only; keyword domain scoring can still select personas (by design of current lock). Tighten if product requires fully fixed persona identity.
4. **Existing persona unit tests** assume registry personas (`legal`, `grunge`, etc.); require `registry.yaml` or fallback registry present.
