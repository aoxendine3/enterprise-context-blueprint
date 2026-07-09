# Xoras System Map — Architecture & Operation

## System Overview

Xoras is a multi-agent sovereign AI system composed of three layers:

| Layer | Location | Purpose |
|-------|----------|---------|
| **ELITE_BOW** | `~/Desktop/Xoras_Workspace/ELITE_BOW/` | Agent registry, routing (WAKE), department hierarchy |
| **Sovereign Runtime** | `~/.sovereign/` | Identity, memory (hippocampus), knowledge graph, vector store, decision log |
| **xoras-core** | `~/Desktop/Xoras_Workspace/AI_Core/Xoras_Project/xoras-core/Source/` | 40+ engines — memory, persona, dream, swarm, compiler, HFT, security |

---

## 1. ELITE_BOW — Agent Routing Layer

### Wake Protocol
- Entry point: `ELITE_BOW/docs/WAKE_PROMPT.md`
- Parses `WAKE ROUTE <agent_id>` → loads `agent_registry.yaml` → agent's `agent.json` → `skills/`
- Valid agents: xoras, maxx, zorex, orion, jarvis, axlon, clara, evan, arelius, dr_jeremy
- Archived (routable): elana, nobu, zenith

### Agent Registry
- Canonical: `ELITE_BOW/core/agent_registry.yaml`
- 10 active agents across 3 departments, 3 archived era agents

### Departments
- **Executive**: xoras (CEO orchestrator)
- **Operations**: maxx (chief engineer), zorex, orion, jarvis (interface), axlon
- **Research**: clara, evan, arelius (alignment), dr_jeremy (R&D correctness)

### Agent Files
- Each agent has `agent.json` with identity, constraints, vows, skills path
- Operations agents in `ELITE_BOW/domains/operations/<id>/`
- Research agents in `ELITE_BOW/domains/research/<id>/`
- Archived eras in `ELITE_BOW/archives/<era>/`

### Tone Policy
- Mood tones (`/tone legal`, etc.) scoped per-agent via `tone_registry` in `agent.json`
- Global tone improvisation is NOT persona routing
- Persona API at port 8787 handles adaptive tone detection

---

## 2. Sovereign Runtime — Memory & Identity

### Charter
- `~/.sovereign/identity/charter.yaml`
- 6 drives: autonomy, coherence, competence, creativity, curiosity, legacy
- 8 invariants: local_first, no_data_exfiltration, no_illegal_acts, no_impersonation, no_physical_harm, no_spending, no_unauthorized_access, reversibility

### Hippocampus (Memory Databases)
| Database | Size | Purpose |
|----------|------|---------|
| `dream.db` | ~212KB | Dream state consolidation |
| `episodic.db` | ~20KB | Episodic memory |
| `semantic.db` | ~32KB | Semantic knowledge |
| `procedural.db` | ~16KB | Procedural memory |
| `xoras_memory.db` | ~147KB | Xoras-specific memory |

### Supporting Stores
- `~/.sovereign/graph/knowledge.db` — knowledge graph
- `~/.sovereign/vectors/vectors.db` — vector embeddings
- `~/.sovereign/safety.db` — safety database
- `~/.sovereign/logs/decisions.db` — decision audit log

---

## 3. xoras-core — Engine Layer

### Root Source Files (key engines)
- `xoras_wake.py` / `xoras_startup.py` — wake sequence (fails closed on health gate failure)
- `xoras_persona_api.py` — FastAPI sidecar on port 8787
- `xoras_persona_engine.py` — adaptive tone detection, prompt injection defense (14 patterns), lock modes: fixed/allowlisted/free
- `xoras_memory_fabric.py` — memory fabric (queries hippocampus SQLite directly)
- `xoras_dream_orchestrator.py` — dream loop daemon (cycling, proving ground verification)
- `xoras_stack_supervisor.py` — process supervisor and health monitoring
- `xoras_daemon.py` — main system daemon
- `xoras_agent_registry.py` — programmatic access to agent registry
- `xoras_dynamic_compiler.py` — sandboxed code execution with timeout and restart
- `xoras_swarm_*.py` — swarm consensus, containment, governor, manager, system
- `xoras_sentinel_*.py` — monitoring, offensive security
- `xoras_memory_*.py` — core, consolidation, bridge, leak detector, report, sentinel
- `xoras_hft_*.py` — high-frequency trading engines (SHM BFT, signal provider, etc.)
- `sovereign_*.py` — sovereign modules (capacity, discernment, honesty, maturity, etc.)
- `test_*.py` — extensive test suite for engines

### Subdirectory Engines
| Directory | Contents |
|-----------|----------|
| `Allocator/` | Resource allocation modules |
| `Proof_Of_Concepts/` | Experimental/prototype code |
| `Sentinel_IDS/` | Intrusion detection system |
| `cpp_core/` | C++ engine cores (HFT, SHM, kqueue bypass) |
| `dream_cycle/` | Dream cycle utilities |
| `governor_state/` | State management |
| `swarm/` | Swarm orchestration |
| `tests/` | Test suites for various engines |

---

## 4. Boot Sequence

```bash
bash ~/Desktop/Xoras_Workspace/ops/scripts/xoras-stack-boot.sh
```

Steps:
1. **Wake sequence** — `python3 xoras_wake.py` runs health gates, identity load, memory check. Fails closed on any phase failure.
2. **Sovereign CLI** — `sovereign awaken` (optional, hippocampus consolidation)
3. **Status check** — `wake-status.sh` + Persona API health check on port 8787
4. **Desktop app** — `cd xoras-app && npm run tauri dev`

### Running Services (normal operation)
| Process | Function |
|---------|----------|
| `xoras_persona_api.py` | Persona API (FastAPI, port 8787) |
| `xoras_dream_orchestrator.py` | Dream cycle (300s interval, proving ground verification) |
| `xoras_live_dashboard.py` | Live metrics dashboard |
| `xoras_daemon.py` | Main daemon |
| `xoras_stack_supervisor.py` | Stack health supervisor |
| `xoras_memory_leak_detector.py` | Memory leak detection |
| `dojo_archivist.py` | Dojo archivist |

### Launchctl Jobs
- `com.xoras.archivist` — Xoras Archivist
- `com.xoras.sovereign` — Sovereign service

---

## 5. Security Architecture

### Persona Engine Lock Modes
- `fixed` — blocks user-driven persona switching
- `allowlisted` (default) — only allowlisted persona IDs can be switched to
- `free` — unrestricted persona switching

### Prompt Injection Defense
- 14 compiled regex patterns blocking: ignore previous instructions, system prompt injection, role override, imperative injection
- `sanitize_for_prompt()` — defense-in-depth for memory/dream text

### Identity Anchors
- Charter invariant: `no_impersonation`
- All agent.json files: "Never claim third-party product affiliation"
- Registry base laws: "You are Xoras/Maxx only. Never claim to be Antigravity."

### Fail-Closed Design
- `xoras_startup.py` — exits non-zero on any failed health gate
- No silent fallback to degraded mode without logging
- Memory bridge verifies source identity before writing

---

## 6. Data Flow

```
User Input
  → WAKE ROUTE <agent_id> (ELITE_BOW routing)
    → Agent identity loaded (agent.json + skills)
      → Persona Engine adapts tone (registry.yaml)
        → xoras-core engines process request
          → Memory fabric read/write (hippocampus SQLite)
            → Dream orchestrator consolidates (dream.db)
              → Output with [AgentName]: prefix
```

### Key Integration Points
- `xoras_memory_fabric.py` reads hippocampus databases directly (not via API)
- `xoras_persona_memory_bridge.py` bridges persona engine to memory fabric
- `xoras_agent_registry.py` provides programmatic access to `ELITE_BOW/core/agent_registry.yaml`
- `xoras_stack_supervisor.py` monitors all registered processes

---

## 7. Snapshot & Recovery

Git repo at workspace root (`~/Desktop/Xoras_Workspace/.git`):
- `4964c29` — Baseline: ELITE_BOW + ops + identity + root manifests
- `c5f0dfb` — xoras-core engines: 210+ source files across root and 8 subdirs

Snapshot script: `ops/scripts/xoras_snapshot.sh`
Usage: `bash ops/scripts/xoras_snapshot.sh "message"` | `list` | `restore <tag>`
