# Orchestration Plan: Single-Prompt OS Build (FreeDoom Target) — Lead 9 Council Mapping

**Status:** REVISED after adversarial review (Vance / NoBoo): 7 MAJOR + 6 MINOR corrected, 0 BLOCKER
**Owner (Orchestrator):** Maxx
**Date:** 2026-10-06

---

## 1. What is actually known about Google's run

| Fact | Source status |
|---|---|
| Human-facing ask: build a functional OS capable of running FreeDoom (kernel, process + memory mgmt, filesystem, video + keyboard drivers) | Blog paraphrase. **Literal prompt never published.** |
| 93 subagents, >15,000 model requests, ~2.6B total tokens, <$1,000, ~12 h wall clock | Reported (I/O 2026 keynote / developer documentation) |
| Exact figures 15,314 calls / 339M input tokens / $916.92 | **Unverified.** No primary URL found. Do not cite. |
| Trigger `/teamwork-preview`; seven roles Sentinel / Orchestrator / Explorer / Worker / Reviewer / Critic / Auditor | Reported (secondary source). Primary URL pending. |
| "Thousands of lines of agent definitions and hooks" | **Not found in sources.** Withdrawn. Sources describe dynamic subagents, sidecars, and generative UI. |

These are reference scale, not targets we claim to have met.

---

## 2. Role mapping (from `Xoras_agent_cards/` only)

| Google role | Function | Assignment | Basis (card) |
|---|---|---|---|
| **Sentinel** | Structures intent, supervises, respawns hung agents | **Jarvis** (chair) + **John** (telemetry) | Governance and arbitration; M4 power, thermal, memory bus |
| **Orchestrator** | Splits work into milestones, never writes code, writes handoff files, hands off to a successor on context fill | **Maxx** | Operations Lead and SSOT Orchestrator |
| **Explorer** | Strategy and prior art | **Clara** + **Sophia** | Research lead; epistemic truth |
| **Worker** | Writes and builds code | **DAXX** (lead), **Zorex**, **Axlon** | Coding specialist; execution; substrate |
| **Reviewer** | Design check | **Aurelius** | Synthesis and auditing |
| **Critic** | Adversarial tests | **William Vance** | Falsification lead |
| **Auditor** | Catches hardcoded outputs and faked receipts | **NoBoo** + **SIA Core** | Bias stripper; swarm integrity |
| Scribe | Handoff and progress files | **Evan** | Systematic recorder |
| Licensing | License compatibility | **Lex** | Legal and compliance |
| Audio | Dispatch routing | **Orion** via `core/ops/scripts/agent_speak.sh` | Single voice daemon |

> [!IMPORTANT]
> The Auditor role directly targets the four defect classes observed this session: hardcoded PASS dicts, a pre-dated timestamp, invented fold scores, and an empty-string SHA-256 presented as a receipt hash.

---

## 3. Reconstructed human prompt (ours; Google's literal text is unpublished)

```
/teamwork-preview
Build a functional x86_64 operating system from scratch that boots in QEMU and runs FreeDoom.
Scope: Limine/Multiboot2 boot handoff, kernel, physical + virtual memory management,
preemptive scheduling with at least one user-mode process, a filesystem able to load
freedoom1.wad, 32bpp framebuffer driver, PS/2 keyboard driver, syscall layer, and a minimal
libc sufficient to build doomgeneric as a separate user-space ELF.
Constraints:
- Host: Apple Silicon M4, macOS. x86_64 guest runs under QEMU TCG (no HVF); tolerate timer jitter.
- Free disk ~5.3 GiB. Halt Worker builds below 1.5 GiB free. USB relocation only on explicit user approval.
- Every milestone ships a headless QEMU test producing a serial log or `screendump -f png` artifact.
- No hardcoded outputs. No receipt without the command, timestamp, and artifact SHA-256 that produced it.
- Orchestrator never writes code; it writes milestone specs and handoff files to docs/plans/teamwork/.
- Progress files updated every task; stale > 15 min = hung, Sentinel respawns.
- Done = FreeDoom title screen captured from QEMU, and scripted key input moves the player.
```

---

## 4. Milestones

| # | Milestone | Exit evidence (Auditor regenerates it from the logged command) |
|---|---|---|
| M0 | `brew install x86_64-elf-gcc x86_64-elf-binutils qemu nasm xorriso` (arm64 bottles, needs Xcode CLT) | Versions logged; QEMU boots an empty Limine image |
| M1 | Kernel entry, serial console, GDT/IDT, exception handlers | `-serial stdio` log line from the kernel |
| M2 | Physical page allocator + paging | Alloc/free stress results over serial |
| M3 | Heap, PIT/APIC timer (ms tick), preemptive kernel-thread scheduler | Two threads interleaving output |
| M3b | User mode (ring 3), ELF loader, syscall entry | User ELF prints via syscall |
| M4 | 32bpp Limine framebuffer driver | `screendump -f png` test pattern (QEMU ≥ 7.1, else PPM→PNG) |
| M5 | PS/2 driver: scancode → doomkey with key-down and key-up | Scripted `sendkey` reflected in serial log |
| M6 | Read-only FS (initrd tar or FAT) | `freedoom1.wad` header `IWAD` logged |
| M7 | libc: malloc/calloc/realloc/free; mem*/str* incl. strcasecmp, strncasecmp, strdup, strstr; ctype; printf, fprintf, snprintf, vsnprintf, sscanf; atoi, atof, abs; fopen, fread, fwrite, fseek, ftell, fclose; exit; stubs for mkdir/remove/rename | doomgeneric links as a user ELF |
| M8 | doomgeneric platform layer: DG_Init, DG_DrawFrame (blit DOOMGENERIC_RESX×RESY, default 640×400, into framebuffer), DG_SleepMs, DG_GetTicksMs, DG_GetKey; DG_SetWindowTitle optional; loop `doomgeneric_Create()` → `doomgeneric_Tick()` | Title-screen PNG; scripted input moves player |

Vance attacks each milestone before Maxx can mark it done. NoBoo and SIA Core reject any evidence they cannot regenerate.

---

## 5. Disk budget

| Item | Approx. |
|---|---|
| Homebrew bottles (cross GCC, binutils, QEMU, nasm, xorriso + deps) | ~1–1.5 GB |
| Homebrew cache (`~/Library/Caches/Homebrew`, clear after install) | transient |
| doomgeneric source + `freedoom1.wad` (~28 MB) | < 100 MB |
| Build artifacts and disk images | < 300 MB |
| **Total** | **≈ 1.8 GB of 5.3 GiB free** |

John checks `df -h /` at every gate. One threshold: below 1.5 GiB free, Worker builds halt. Relocating to USB requires explicit user approval (USB is backup only, by directive).

---

## 6. Scale gap

Google ran 93 subagents and >15k requests as a managed `/teamwork-preview` job. Our in-session swarm is far smaller. The full build is meant to run by launching `/teamwork-preview` with the §3 prompt. Within this session the Council targets M0–M2. A milestone counts as delivered only when its §4 evidence passes Auditor regeneration.

---

## 7. Licensing (Lex; verified)

- **FreeDoom:** BSD-3-Clause. Redistributable with copyright notice and license text retained; no endorsement use.
- **doomgeneric:** GPL-2.0. If linked into the kernel image, the **entire image** is a GPL-2.0 combined work. The kernel can keep its own license only if the engine is a separate user-space ELF loaded through syscalls, which is why M3b exists.

---

## 8. Review receipt

- Critic/Auditor subagent: `56025034-a833-4d42-a9b0-318a239da689`. Read-only review returned 13 defects; all applied in this revision.
