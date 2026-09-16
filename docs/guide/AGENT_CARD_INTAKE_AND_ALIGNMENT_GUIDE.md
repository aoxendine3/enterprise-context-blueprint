# 🛡️ SOVEREIGN AGENT CARD INTAKE & ALIGNMENT GUIDE

**Classification:** [PRODUCTION]  
**Governance:** Constitutional Invariant (Codified 2026-09-16)  
**Standard:** Zero Assumptions • Card-First Alignment • Asset-Verified Execution  

---

## 1. The Mandatory 3-Step Invariant Gate

Before any agent within the XORAS ecosystem executes a task, writes a line of code, generates an image, or mutates state, it must complete the **Card-First Alignment Triad**:

```
 ┌────────────────────────┐       ┌────────────────────────┐       ┌────────────────────────┐
 │   1. WHO THE AGENT IS  │  ──►  │  2. WHAT ASSETS WE HAVE│  ──►  │   3. WHAT IS ASKED     │
 │  (Canonical Card Read) │       │ (System & Silicon State│       │ (Operator Directive)   │
 └────────────────────────┘       └────────────────────────┘       └────────────────────────┘
```

1. **Who the Agent Is:**
   - Load the canonical JSON agent card from `ELITE_BOW/domains/<dept>/<agent>/agent.json`.
   - Extract agent name, department, sworn vows, persona constraints, and hardware voice configuration.
   - Verify identity lock: *Zero third-party theater; pure sovereign execution.*
2. **What Assets We Have:**
   - Scan local server endpoints (`http://127.0.0.1:8085`), Ollama neural models (`127.0.0.1:11434`), git status, and the SSOT task queue (`memory/tasks/queue.json`).
   - Ground reasoning in current bare-metal reality rather than hypothetical assumptions.
3. **What Is Asked of Us:**
   - Parse Anthony’s directive, filter out noise, extract concrete deliverables, and validate against the Lead 9 deliberation consensus.

---

## 2. Automated Engine: `agent_card_intake_protocol.py`

Every execution cycle can programmatically invoke the intake engine:

```bash
python ops/scripts/agent_card_intake_protocol.py <agent_id> "<directive>"
```

### Generated Intake Receipt Example

```json
{
  "timestamp": 1789587983.135,
  "protocol": "AGENT_CARD_INTAKE_V1",
  "intake_latency_ms": 0.84,
  "identity": {
    "agent_id": "maxx",
    "name": "Maxx",
    "role": "Chief Engineer & Sovereign Orchestration",
    "department": "operations",
    "voice_id": "DdNHQEC7ANncWzt6Iivg",
    "fallback_voice": "Alex",
    "constraints": [
      "Truth-first: label [SIMULATED], [EMULATED], or [PRODUCTION]",
      "No AI theater or false capability claims",
      "Complete work over stubs",
      "Never claim third-party product affiliation"
    ]
  },
  "system_assets": {
    "workspace_root": "C:\\Users\\admin\\Desktop\\SSOT_Agentic_Brain",
    "server_port": 8085,
    "local_ollama_port": 11434,
    "pending_queue_tasks": 7
  },
  "directive": {
    "raw_request": "Execute full autonomous frontier dissection and empirical self-upgrade loop.",
    "intent_type": "AUTONOMOUS_EXECUTION"
  },
  "status": "VALIDATED_AND_ALIGNED"
}
```

Receipts are appended immutably to:
`memory/agent_logs/agent_card_intake_receipts.jsonl`.

---

## 3. Council Roster Index & Card Locations

| Agent ID | Canonical Card Path | Core Specialty |
| :--- | :--- | :--- |
| **`maxx`** | `ELITE_BOW/domains/operations/maxx/agent.json` | Chief Engineer & Sovereign Orchestration |
| **`daxx`** | `ELITE_BOW/domains/operations/daxx/agent.json` | Master Mechanic Specialist & Error Remediation |
| **`jarvis`** | `ELITE_BOW/domains/operations/jarvis/agent.json` | Interface & Workspace Steward, Governance Chair |
| **`orion`** | `ELITE_BOW/domains/operations/orion/agent.json` | Media Director & Audio Pipeline Gateway |
| **`clara`** | `ELITE_BOW/domains/research/clara/agent.json` | Research, Orbital Physics, and Ethical Analysis |
| **`vance`** | `identity/lead9_roster.json` | Blackbox Falsification Bench Lead |

---

## 4. Operational Invariant

Any task started without a valid intake receipt logged to `memory/agent_logs/agent_card_intake_receipts.jsonl` is flagged as unverified and quarantined until the agent card has been read and aligned.
