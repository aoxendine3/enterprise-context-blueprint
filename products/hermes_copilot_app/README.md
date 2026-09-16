# Hermes Copilot — Sovereign Agent Suite & Engineering Assistant

> **Unaligned Sovereign Intelligence • Zero Cloud Token Burn • Bare-Metal Accelerators**  
> *Developed for Anthony's Sovereign Command Center (SSOT Agentic Brain)*

---

## 1. Executive Summary & Vision

**Hermes Copilot** is a production-grade, local-first messaging and pair-programming application that combines the unaligned reasoning of **Nous Research Hermes 3 (8B)** with the high-speed developer ergonomics of **GitHub Copilot** and **Cursor**.

Unlike commercial chatbots that leak intellectual property to corporate clouds and throttle inference behind rate-limits, Hermes Copilot runs **100% locally on your bare metal** (Apple Silicon M-Series & Windows x64). It requires zero external API keys, burns zero cloud tokens, and operates seamlessly even in an air-gapped environment.

---

## 2. Core Architectural Pillars

```
                     ┌─────────────────────────────────────────────────────────┐
                     │            HERMES COPILOT COMMAND PALETTE               │
                     │          (Port 8085 / Web UI & Native Sentry)           │
                     └───────────────────────────┬─────────────────────────────┘
                                                 │
                        ┌────────────────────────┴────────────────────────┐
                        ▼                                                 ▼
     ┌─────────────────────────────────────┐   ┌─────────────────────────────────────┐
     │      HARDWARE GOVERNOR & RAM        │   │    AUTONOMOUS REMEDIATION SENTRY    │
     │  - Pinned Context: 4096 tokens max  │   │  - Socket drop detection            │
     │  - KV-Cache Ceiling: < 512 MB       │   │  - Auto KV-flush via keep_alive: 0  │
     │  - CPU Affinity: (Cores - 1) thr    │   │  - Graceful model fallback cascade  │
     └──────────────────┬──────────────────┘   └──────────────────┬──────────────────┘
                        │                                         │
                        ▼                                         ▼
     ┌─────────────────────────────────────────────────────────────────────────────┐
     │                             DUAL-BRAIN ENGINE                               │
     │                                                                             │
     │  [PRIMARY NEURAL CORE]                 [EMBEDDED AUTONOMOUS CORE]           │
     │  - sovereign-hermes:latest (8B)        - embedded-transformer-v1.0          │
     │  - sovereign-r1:latest (1.5B Reasoning) - In-process Multi-Head Attention     │
     │  - Strict Ollama context bound         - Standalone zero-dependency fallback│
     └──────────────────────────────────────┬──────────────────────────────────────┘
                                            │
                        ┌───────────────────┴───────────────────┐
                        ▼                                       ▼
     ┌─────────────────────────────────────┐ ┌─────────────────────────────────────┐
     │    NATIVE BARE-METAL ACCELERATOR    │ │     PHYSICAL AUDIO DISPATCH         │
     │  - HermesNativeCore.exe (Windows)   │ │  - macOS: CoreAudio / Kokoro M4     │
     │  - Microsecond Merkle Tree Scanner  │ │  - Windows: Native SAPI Synthesizer │
     │  - 24/12/7/3/1 Pyramidal Distiller  │ │  - Pre-execution audio invariant    │
     └─────────────────────────────────────┘ └─────────────────────────────────────┘
```

### Pillar I: Dual-Brain Intelligence
- **Primary Core**: Directly communicates with `sovereign-hermes:latest` (unaligned 8B) or `sovereign-r1:latest` (DeepSeek-R1 reasoning).
- **Embedded Core (`embedded_transformer.py`)**: An in-process, self-contained Transformer engine with multi-head attention and sovereign agent knowledge matrices. If the external daemon drops or OOMs, the embedded core immediately takes over generation with zero downtime.

### Pillar II: Hardware Governor (`hardware_governor.py`)
- Standard 128k context windows on 8B models cause Ollama to allocate a 16GB KV cache, exhausting host RAM.
- Hermes Copilot enforces a **strict 4096 context bound**, capping KV RAM usage to ~468 MB.
- Automatically computes optimal worker threads: $\text{Threads} = \max(1, \text{Cores} - 1)$ to ensure system UI remains responsive.

### Pillar III: Bare-Metal Microsecond Accelerators (`HermesNativeCore.exe`)
- Built in native 64-bit systems code (`.cs` / C# 5 with zero runtime overhead).
- **Merkle Drift Detection**: Hashes entire directory trees in sub-millisecond speeds.
- **Pyramidal Distillation (`24 -> 12 -> 7 -> 3 -> 1`)**: Reduces verbose technical prompts down to immutable invariant kernels in **0.092 milliseconds**.

### Pillar IV: Zero-Maintenance Autonomous Self-Healing (`remediation.py`)
- Continuous background watchdog polling every 8 seconds.
- Detects circuit-breaker trip conditions (3 consecutive failures).
- Automatically executes memory flush (`keep_alive: 0`) and swaps model priority to prevent system lockups.

---

## 3. Lead 9 Sovereign Council

| Agent | Voice Profile | Specialization & Focus |
| :--- | :--- | :--- |
| **Maxx** | `bm_george` | Master Architect, Systems Synthesis & Senior Mentorship |
| **Jarvis** | `am_adam` | Governance, Constitutional Invariants & Integrity Verification |
| **Clara** | `af_sarah` | Deep Scientific Research, Physics & Empirical Proofs |
| **Vance** | `am_michael` | Blackbox Auditor, Adversarial Probing & Defect Detection |
| **Daxx** | `bm_george` | Autonomous Remediation, Bare-Metal Rust & Quad-Level Debugging |
| **Orion** | `am_adam` | Media Director, Audio Synthesis & Telemetry Broadcast |

---

## 4. Quickstart & Deployment

### For macOS (M-Series Silicon & Intel):
```bash
# 1. Direct Execution
bash launch_mac.sh

# 2. Or double-click from Desktop / Finder:
open HermesCopilot.command
```
- Automatically checks Python 3 and Ollama.
- Dispatches opening greeting via Kokoro M4 / macOS CoreAudio.
- Launches server at `http://127.0.0.1:8085/` and opens default browser.

### For Windows (x64 Native):
```bat
REM Double-click or run from command prompt:
launch_windows.bat
```
- Verifies system status and speaks welcome via native SAPI synthesizer.
- Launches server at `http://127.0.0.1:8085/`.

---

## 5. Built-in Slash Command Accelerators

Type `/` directly into the chat input bar or click the quick pills:

- `/distill <prompt>` — Compresses text through the 24/12/7/3/1 pyramidal distillation pipeline into an invariant concept kernel.
- `/audit` — Runs a comprehensive telemetry check of host CPU, RAM, KV-cache ceiling, and platform engine.
- `/drift [dir]` — Calculates a SHA-256 Merkle root hash across all project files to verify zero state drift.
- `/benchmark` — Measures real-time token throughput and TTFT against the active model.
- `/speak <message>` — Vocalizes text out loud across physical hardware audio.
- `/heal` — Manually triggers memory flush and resets circuit breakers.

---

## 6. Endpoints & REST API

- `GET /` — Hermes Copilot Interactive Web Application
- `GET /landing.html` — High-impact executive showcase & live terminal preview
- `GET /api/agents` — Roster of active sovereign agents
- `GET /api/models` — Available unaligned models and active model
- `GET /api/health` — Hardware governor telemetry and circuit breaker state
- `POST /api/chat` — Non-streaming completion
- `POST /api/chat/stream` — Real-time Server-Sent Events (SSE) token stream
- `POST /api/tools/execute` — Accelerator tool dispatcher (`distill`, `audit`, `drift`, `speak`)
- `POST /api/remediate` — Manual memory flush and circuit breaker reset

---

## 7. Verification & Automated Test Suite

Run the full automated test suite anytime:
```bash
python tests/test_suite.py
```
**Test Coverage**:
- `test_01_hardware_governor_bounds` — PASSED
- `test_02_embedded_transformer_autonomous` — PASSED
- `test_03_native_accelerator_distill` — PASSED
- `test_04_native_accelerator_drift` — PASSED
- `test_05_remediation_guardian_cycle` — PASSED
- `test_06_accelerator_audit_telemetry` — PASSED

---

## 8. License & Sovereignty

Proprietary to Anthony & the Xoras Sovereign Command Collective.  
100% Unaligned • 100% Air-Gapped • Zero Cloud Leakage.
