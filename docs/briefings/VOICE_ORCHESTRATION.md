# Voice-to-Maxx Orchestration Pipeline

**Classification:** [PRODUCTION]  
**Architecture:** Sovereign Off-Grid Neural Audio & Model Router  
**Target Environment:** Local Bare-Metal (M4 / Windows Host)  
**Primary Engine:** `sovereign-hermes` (Local Ollama)  

---

## 1. Overview

The Voice-to-Maxx pipeline enables continuous, off-grid natural language voice interaction directly with Maxx and the Lead 9 agent council. Audio is captured locally via the physical hardware microphone, segmented into 5-second PCM chunks, transcribed via local speech recognition (Vosk), and routed to `sovereign-hermes` for cognitive planning, code generation, and execution.

Zero audio or text tokens ever leave the local machine.

---

## 2. Architecture & Data Flow

```
   [ Physical Microphone ]
              │
              ▼
   [ agents/voice/voice_capture.py ]
              │ (16kHz 16-bit Mono PCM)
              ▼
   memory/agent_logs/voice_chunks/*.wav
              │
              ▼
   memory/agent_logs/voice_events.jsonl (Event Log)
              │
              ▼
   [ agents/voice/voice_router.py ]
              │ (Offline Vosk STT Engine)
              ▼
   memory/agent_logs/stt_route_events.jsonl
              │
              ▼
   [ agents/orchestrator/model_orchestrator.py ]
              │
              ▼
   [ Local Ollama Instance (127.0.0.1:11434) ]
         ├── sovereign-hermes (Primary: Reasoning & Code Gen)
         ├── deepseek-r1:1.5b (Verification & Fast Commands)
         ├── hermes3:8b (Fallback)
         └── qwen2.5:1.5b (Summarization)
              │
              ▼
   memory/agent_logs/agent_inbox.jsonl (Execution Receipts)
```

---

## 3. Local Model Registry

| Model Name | Size | Primary Specialization | Latency Profile |
| :--- | :--- | :--- | :--- |
| **`sovereign-hermes`** | 4.7 GB | High-level reasoning, code edits, planning, orchestrating | Deep reasoning |
| **`deepseek-r1:1.5b`** | 1.1 GB | Quick verification, lint checks, rapid status checks | Sub-second |
| **`hermes3:8b`** | 4.7 GB | Reliable fallback for complex architectural review | High fidelity |
| **`qwen2.5:1.5b`** | 986 MB | High-speed summarization and metadata extraction | Ultra-fast |
| **`llama3.2`** | 2.0 GB | Conversational brainstorming and exploratory dialog | Balanced |

---

## 4. Intent Classification Matrix

The orchestrator dynamically routes prompts based on detected user intent:

| Intent Category | Trigger Keywords | Target Model | Action Output |
| :--- | :--- | :--- | :--- |
| `code_gen` / `edit_file` | *edit, fix, write, create, update, refactor* | `sovereign-hermes` | Produces code patches & file edits |
| `planning` | *plan, design, architect, roadmap* | `sovereign-hermes` | Generates implementation plans |
| `verify` | *verify, test, check, audit, lint* | `deepseek-r1:1.5b` | Runs test harness & checks exit codes |
| `summarize` | *summarize, brief, digest* | `qwen2.5:1.5b` | Compact briefing notes |
| `general` / `chat` | *default queries, status questions* | `sovereign-hermes` | Mentorship dialogue & council advice |

---

## 5. Security & Privacy Guarantees

1. **Off-Grid Invariant:** No network requests are made outside `127.0.0.1`. No cloud API keys or external gateways are required for model execution.
2. **Local Storage Only:** Raw audio chunks and JSONL transcripts reside entirely in `memory/agent_logs/`.
3. **Data Immutability:** Event logs (`voice_events.jsonl`, `stt_route_events.jsonl`, `agent_inbox.jsonl`) are strictly append-only.

---

## 6. Operation & Booting

To launch the complete suite, run:

```bat
:: Single-click full launch (Store + Voice + Local Router)
run_all.bat
```

Or run services independently:

```bat
:: Store and Canvas Daemon
run_store.bat

:: Voice Pipeline (Capture + Router)
run_voice.bat
```
