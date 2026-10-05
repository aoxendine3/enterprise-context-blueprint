# ENGINEERING AUDIT: Audio Fallback Purge Post-Mortem
**DATE:** 2026-10-02
**AUTHOR:** Jarvis (Governance AI) / Xoras Sovereign Collective
**TARGET:** Purged audio override scripts (`direct_speak.sh`, `safe_agent_speak.sh`, `kokoro_direct_play.py`)

## Executive Summary
Per the canonical command of the User, experimental and fallback audio scripts have been moved to `archives/the_barn/audio_conflicts/`. This audit documents their behavior to establish a clear root cause for the `libc++abi: std::__1::system_error: recursive_mutex lock failed` crashes observed in the Kokoro M4 synthesis engine, and prevents future regressions.

## 1. Analysis of Purged Files

### A. `direct_speak.sh`
- **Behavior**: Called the Kokoro python script directly.
- **The Defect**: Established a rogue lockfile (`/tmp/kokoro_direct_audio.lock`). Because it did not use the canonical `/tmp/coreaudio_single_speaker.lockdir`, it could execute concurrently with the main `agent_speak.sh`, causing immediate hardware mutex collisions at the CoreAudio level.

### B. `safe_agent_speak.sh`
- **Behavior**: Attempted to act as a "safe" zero-mutation speaker wrapper.
- **The Defect**: Established a *third* competing lockfile (`/tmp/sovereign_audio_speaker.lock`). This completely bypassed the media director's queue and failed to respect the canonical audio state, leading to identical overlap crashes.

### C. `kokoro_direct_play.py`
- **Behavior**: Bypassed the entire Xoras media pipeline. Initialized the ONNX Kokoro engine in isolation, wrote a raw `.wav` to `/tmp/dr_jeremy_speech.wav`, and executed a synchronous macOS `afplay`.
- **The Defect**: By bypassing the `sync_stage_engine_kokoro.py` and `media_director_agent.py` processes, it starved the primary queue of resources and ignored all system-level audio locks. 

## 2. Root Cause of System Crashes
The physical M4 DAC (Digital-to-Analog Converter) and the PyTorch synthesis engine require absolute sequential execution. Because the rogue scripts utilized disparate locking mechanisms, multiple synthesis processes attempted to lock the hardware simultaneously. The macOS kernel rightfully aborted the operations (`Abort trap: 6`) to protect the hardware state.

## 3. The Canonical Resolution
All speech MUST flow exclusively through `/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/agent_speak.sh`. 
This script utilizes the singular `/tmp/coreaudio_single_speaker.lockdir` which properly aligns with the media director queue, ensuring zero lag, zero gaps, and zero overlapping.

**STATUS:** Fallbacks isolated in the barn. Canonical path strictly enforced.
