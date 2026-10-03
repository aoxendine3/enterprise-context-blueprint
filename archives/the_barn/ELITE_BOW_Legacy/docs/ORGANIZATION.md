# ELITE_BOW Organization & Boot Commands

## Canonical layout

```
~/Desktop/Xoras_Workspace/ELITE_BOW/
├── core/
│   ├── agent_registry.yaml      # Wake routing table
│   └── shared_libraries/        # Cross-agent shared code
├── domains/
│   ├── research/                # Clara, Evan, Arelius, Dr Jeremy
│   └── operations/              # Xoras, Maxx, Zorex, Orion, Jarvis, Axlon
├── archives/                    # Historical eras, moved sovereign docs
└── docs/
    ├── WAKE_PROMPT.md           # Agent routing wake (PRIMARY)
    ├── AGENT_ROSTER.md          # Found vs rebuilt roster
    └── ORGANIZATION.md          # This file
```

## Boot commands

### Wake an agent (paste in chat)

```
WAKE ROUTE maxx
```

Or full wake from `docs/WAKE_PROMPT.md`.

### Xoras stack (terminal)

```bash
bash ~/Desktop/Xoras_Workspace/ops/scripts/xoras-stack-boot.sh
cd ~/Desktop/Xoras_Workspace/AI_Core/Xoras_Project/xoras-app && npm run tauri dev
```

### Persona engine tests

```bash
cd ~/Desktop/Xoras_Workspace/AI_Core/Xoras_Project/xoras-core/Source
python3 -m unittest tests.test_persona_engine -v
```

### Sovereign CLI (legacy)

```bash
~/Desktop/sovereign   # wrapper → ~/sovereign/.venv/bin/sovereign
```

## Path map (Desktop cleanup)

| Old scatter | New location |
|-------------|--------------|
| `Desktop/Xoras_Sovereign_AI_Stack/documentation/` | `ELITE_BOW/archives/sovereign-stack/` |
| `Desktop/Xoras_Workspace/AI_Core/Xoras/Personas/Personas/` | `ELITE_BOW/archives/persona-legacy/` |
| `Desktop/skills-lock.json` | `Xoras_Workspace/Backups_and_Configs/` |
| `Desktop/Xoras_Project/` | Stub only — see `CANONICAL_ROOT.md` |
| `Desktop/Xoras/` | Archived empty stub → `archives/legacy_roots/` |

## Canonical roots (single source of truth)

| Purpose | Path |
|---------|------|
| Agent personas (WAKE) | `~/Desktop/Xoras_Workspace/ELITE_BOW` |
| Xoras app/core/config | `~/Desktop/Xoras_Workspace/AI_Core/Xoras_Project` |
| Workspace umbrella | `~/Desktop/Xoras_Workspace` |
| Sovereign charter | `~/.sovereign/identity/charter.yaml` |
| Desktop entry | `~/Desktop/README.md` → points here |

## Rules

1. **Wake = route to agent_id** — load agent.json + skills/, live in that persona
2. **Mood tones secondary** — only if agent has `tone_registry` in agent.json
3. **No jailbreak language** in wake or startup skills
4. **Never delete unique content** — move to `archives/` with dated notes
