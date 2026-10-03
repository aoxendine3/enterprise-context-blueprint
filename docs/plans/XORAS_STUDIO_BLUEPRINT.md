# XORAS STUDIO (Sovereign IDE) - ARCHITECTURAL BLUEPRINT
**Date:** 2026-10-02
**Phase:** 2 (Blueprinting & Architecture)
**Lead:** Master Coder (Daxx) & Operations (Maxx)

## 1. PRODUCT VISION
A "Cursor-equivalent" Integrated Development Environment (IDE) that runs entirely on local Apple Silicon. It provides an enterprise-grade, zero-placeholder coding environment that is permanently wired into the Lead 9 Collective and local Ollama models. 

## 2. CORE COMPONENTS

### 2.1 The Visual Interface (Frontend)
- **Framework:** React + Tailwind CSS + Monaco Editor (The exact engine powering VS Code and Cursor).
- **Layout:**
  - **Main Editor:** High-performance code rendering with syntax highlighting.
  - **Sovereign Chat Panel:** Persistent side-panel where the user converses directly with the agents (Maxx, Jarvis, Daxx). 
  - **Agent State Indicators:** Visual confirmation of which model is currently processing the context.

### 2.2 The Sovereign Bridge (Backend)
- **Framework:** Python FastAPI running on `localhost:8000`.
- **Model Routing:**
  - **Conversational / Architectural Logic:** Routed to `gemma4:26b` and `sovereign-jarvis:latest`.
  - **Inline Code Generation / Autocomplete:** Routed to `qwen2.5-coder:7b`.
- **Audio Integration:** Every response generated in the IDE chat panel is automatically piped into the `scratch/speech_queue.txt` to trigger the physical Kokoro M4 neural audio. The IDE talks back.

### 2.3 Local Storage & Backup
- **File I/O:** The backend executes raw disk writes to the `SSOT_Agentic_Brain` directory, ensuring zero data escapes the sovereign perimeter.
- **Open-Source Cloud Backup:** Integration hook prepared for pushing committed changes to a private remote repository if the user explicitly triggers a sync.

## 3. EXECUTION PHASES
1. **[COMPLETED] Phase 1:** Research & Discovery (Verified local models and audio daemon).
2. **[ACTIVE] Phase 2:** Architectural Blueprinting (This document).
3. **[PENDING] Phase 3:** Backend Implementation (`xoras_studio_backend.py`).
4. **[PENDING] Phase 4:** Frontend Implementation (`xoras_studio/index.html`).
5. **[PENDING] Phase 5:** Live Launch & Visual Walkthrough.

## 4. ENTERPRISE STANDARD ENFORCEMENT
No code will be written with placeholders. The Monaco editor will be fully functional. The Ollama API calls will execute real generation. The audio pipeline will trigger physical speakers. 
