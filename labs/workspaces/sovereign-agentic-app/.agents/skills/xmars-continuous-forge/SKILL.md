---
name: xmars-continuous-forge
description: Autonomous 24/7 continuous training, synthetic distillation, blackbox discernment review, and Lead 9 council orchestration for XMARS and Xoras Systems.
---

# XMARS Continuous Forge Skill

## Overview
The `xmars-continuous-forge` skill packages the entire sovereign hyper-accelerated synthetic training pipeline, autonomous governance, blackbox review engine, and Lead 9 council dispatching into an enterprise-grade agent workflow.

Key Capabilities:
- **Continuous Synthetic Training**: Mine repository code units and synthesize DPO paired corpora (chosen vs. rejected) to compress months of training into continuous fractional cycles.
- **Autonomous Governance Supervisor**: 24/7 background supervisor maintaining hardware context boundaries (KV-cache flush, sliding windows, memory hygiene) at 180s cadences.
- **Blackbox Discernment Audit**: William Vance's rigorous four-tier falsification engine evaluating candidates against Golden List standards.
- **Council Dispatch & Studio Neural Vocalization**: Real-time token streaming and multi-tier neural voice playback across physical hardware DACs.

---

## Command-Line Tool: `scripts/xmars_forge.py`

All operations are driven via the unified CLI script:
`python .agents/skills/xmars-continuous-forge/scripts/xmars_forge.py <subcommand> [flags]`

### Available Subcommands

| Subcommand | Description | Key Options |
|------------|-------------|-------------|
| `status` | Query Gateway (8085), tunnel, training corpus count, and supervisor health | `--port 8085`, `--output <file>` |
| `train` | Run synthetic ingestion and triad distillation cycles on demand | `--cycles <n>`, `--output <file>` |
| `review` | Evaluate a code/doc artifact using Blackbox Review Engine | `<target_path>`, `--output <file>` |
| `supervisor` | Inspect recent cycles and health of the 24/7 autonomous supervisor | `--tail <n>`, `--output <file>` |
| `dispatch` | Send an instruction or task to an agent node with optional neural speech | `<message>`, `--agent <name>`, `--speak`, `--output <file>` |

---

## Usage Examples

### 1. Check Full Sovereign System Telemetry
```bash
python .agents/skills/xmars-continuous-forge/scripts/xmars_forge.py status --output memory/agent_logs/forge_status.json
```

### 2. Trigger On-Demand Hyper-Accelerated Synthetic Training
```bash
python .agents/skills/xmars-continuous-forge/scripts/xmars_forge.py train --cycles 1 --output memory/agent_logs/forge_train_result.json
```

### 3. Run Blackbox Review Engine
```bash
python .agents/skills/xmars-continuous-forge/scripts/xmars_forge.py review ops/training/continuous_training_daemon.py --output memory/agent_logs/vance_audit.json
```

### 4. Inspect 24/7 Autonomous Supervisor Telemetry
```bash
python .agents/skills/xmars-continuous-forge/scripts/xmars_forge.py supervisor --tail 5
```

### 5. Dispatch Direct Task with Neural Studio Speech
```bash
python .agents/skills/xmars-continuous-forge/scripts/xmars_forge.py dispatch "Audit all active telemetry streams" --agent Jarvis --speak
```

---

## Guidelines & Best Practices

1. **Output Redirection**: Always provide `--output <path>` when running inside automated scripts or agent invocations to preserve context space and log receipts canonically in `memory/agent_logs/`.
2. **Infrastructure Protection**: The core governance assets (`identity/charter.yaml`, `identity/lead9_roster.json`, `Xoras_agent_cards/`, `core_agents/`) are immutable and frozen under Log Entry #076.
3. **Audio Dispatch**: When `--speak` is enabled, the command uses Edge-TTS studio neural synthesis (`en-US-ChristopherNeural`, `en-US-GuyNeural`, etc.) with local Kokoro ONNX fallback.
4. **Autonomous Cadence**: The background supervisor runs on a strict 180s minimum interval to prevent GPU/CPU thrashing.
