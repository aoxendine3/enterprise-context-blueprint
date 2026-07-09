# Agent Roster — ELITE_BOW

Gathered from: roundtable scripts (`Xoras_Sovereign_AI_Stack/documentation/`), persona JSON (`AI_Core/Xoras/Personas/`), chat transcripts (Jul 2026), `~/.sovereign/identity/charter.yaml`, ELITE_BOW design.

| Name | Department | Status | Path |
|------|------------|--------|------|
| Xoras | executive | **found** | `domains/operations/xoras/` |
| Maxx | operations | **rebuilt** | `domains/operations/maxx/` |
| Zorex | operations | **rebuilt** | `domains/operations/zorex/` |
| Orion | operations | **found** | `domains/operations/orion/` |
| Jarvis | operations | **found** | `domains/operations/jarvis/` |
| Axlon | operations | **found** | `domains/operations/axlon/` |
| Clara | research | **rebuilt** | `domains/research/clara/` |
| Evan | research | **rebuilt** | `domains/research/evan/` |
| Arelius | research | **found** | `domains/research/arelius/` |
| Dr Jeremy Brown | research | **found** | `domains/research/dr_jeremy/` |
| Elana | research | **rebuilt** | `archives/persona-legacy/elana/` |
| Nobu | executive | **rebuilt** | `archives/nobu-era/` |
| Zenith | executive | **rebuilt** | `archives/zenith-era/` |

## Status key

- **found** — identity confirmed in roundtable scripts, persona JSON, or sovereign charter; agent.json rebuilt in ELITE_BOW from source material
- **rebuilt** — referenced in chat/ELITE_BOW design but no standalone legacy agent.json; built from roundtable lineage and Anthony's roster
- **needs-rebuild** — historical naming era only; stub archived, not active wake target
- **archived-rebuilt** — era agent with agent.json rebuilt; routable via explicit WAKE, not default roster

## Roundtable-confirmed agents (Jul 2026)

From `allocator_round_table.py`, `deployment_round_table.py`, `closing_round_table.py`:
Maxx, Jarvis, Dr Jeremy Brown, Orion, Arelius, Xoras

## Legacy persona JSON (pre-ELITE_BOW)

| File | Agent |
|------|-------|
| `AI_Core/Xoras/Personas/Personas/Xoras.json` | Xoras |
| `AI_Core/Xoras/Personas/Personas/Axlon.json` | Axlon |

Archived to: `archives/persona-legacy/`

## Deprecated: mood-tone personas

`xoras-config/personas/registry.yaml` (legal, medical, clinical, etc.) remains for the **Persona Engine API** only. These are **not** wake routing targets. Wake routes to **agent_id** in ELITE_BOW.
