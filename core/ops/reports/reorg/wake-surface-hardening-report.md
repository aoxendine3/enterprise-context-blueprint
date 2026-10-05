# Wake Surface Hardening Report

**Date:** 2026-07-04  
**Scope:** Loud, fail-closed wake contract + unmistakable app surface status  
**Runtime:** `AI_Core/Xoras_Project/xoras-core/Source/`  
**App:** `AI_Core/Xoras_Project/xoras-app/`

## Summary

Wake is no longer a quiet log drip. Terminal output uses large phase banners (`IDENTITY → MEMORY → SECURITY → SERVICES → READY`), a live status file is updated each phase, and the desktop app shows a prominent **WAKE: READY / OFFLINE / FAILED / RUNNING** chip. Chat remains fail-open if wake is offline; wake itself stays fail-closed on health gates.

## Files Changed

| File | Change |
|------|--------|
| `Source/xoras_startup.py` | Strong wake contract: banners, `.xoras_wake_status.json`, phase markers in log, READY/FAILED blocks, `persona_lock_mode` |
| `Source/xoras_wake.py` | **New** CLI entry (`python3 xoras_wake.py`) printing `XORAS WAKE SEQUENCE` |
| `xoras-app/src-tauri/src/sys.rs` | `get_wake_status`, `trigger_wake_agents` Tauri commands |
| `xoras-app/src-tauri/src/lib.rs` | Register wake commands |
| `xoras-app/src/lib/api.js` | `getWakeStatus`, `triggerWakeAgents` |
| `xoras-app/src/lib/constants.js` | Wake status/script paths |
| `xoras-app/src/context/AppContext.jsx` | Poll wake status (4s); expose `probeWakeStatus` / `triggerWakeAgents` |
| `xoras-app/src/App.jsx` | Top-bar wake chip + **Wake Agents** button |
| `xoras-app/src/components/SettingsPanel.jsx` | Agent Wake section with chip, lock mode, Wake/Refresh |
| `xoras-app/src/index.css` | Loud wake chip styles (green/amber/red/cyan) |
| `ops/reports/reorg/wake-surface-hardening-report.md` | This report |

**Unchanged:** `Source/xoras_memory_bridge.py` (L2 SHM/Mongo trade-signal bridge intact).

## Wake Contract

Phases (stdout banners + status file + log markers):

1. **IDENTITY** — agents manifest present; record `persona_lock_mode`
2. **MEMORY** — memory watchdog starts and stays alive
3. **SECURITY** — persona lock mode validated; startup lock held
4. **SERVICES** — core daemon + optional dashboard; **fail-closed** health gates (`http://localhost:1420/health`)
5. **READY** — loud success block; status `phase=READY`, `status=ok`

On any failure: status `phase=FAILED`, `status=failed`, loud FAILED block, **exit non-zero**. Startup lock is only released by the process that acquired it.

### Status file

Path: `AI_Core/Xoras_Project/xoras-core/Source/.xoras_wake_status.json`

```json
{
  "phase": "READY",
  "status": "ok",
  "message": "Startup completed; all required health gates passed.",
  "timestamp": "2026-07-04T11:05:12",
  "pid": 12345,
  "persona_lock_mode": "allowlisted"
}
```

`persona_lock_mode` defaults to `allowlisted` (`XORAS_PERSONA_LOCK_MODE` env: `fixed` | `allowlisted` | `free`).

Log: `Source/xoras_startup.log` includes `[PHASE]` markers for the same sequence.

## App Surface

| Surface | Meaning |
|---------|---------|
| **WAKE: READY** (green) | Status file reports READY/ok |
| **WAKE: OFFLINE** (amber) | No status file / unreadable |
| **WAKE: FAILED** (red, pulsing) | Wake wrote FAILED |
| **WAKE: RUNNING** (cyan) | Mid-phase (`status=running`) |

- Top bar chip is always visible; tooltip shows message + lock mode.
- **Wake Agents** (top bar + Settings) launches `python3 xoras_wake.py` in the background and polls status.
- Settings → Agent Wake shows phase detail and lock mode.
- Chat is **fail-open** if wake is offline (status chip only; messaging still works).

## How to Trigger / See Wake

**Terminal (loud):**

```bash
cd AI_Core/Xoras_Project/xoras-core/Source
python3 xoras_wake.py
# or
python3 xoras_startup.py
```

Watch for `XORAS WAKE SEQUENCE` and phase banners, then a final `READY` or `FAILED` block. Inspect:

```bash
cat .xoras_wake_status.json
tail -f xoras_startup.log
```

**App:**

1. Open xoras-app (rebuild Tauri if needed so new commands load).
2. Top bar shows **WAKE: …** chip immediately (polls every 4s).
3. Click **Wake Agents** or Settings → Agent Wake → **Wake Agents**.
4. Chip updates through RUNNING → READY (or FAILED).

## Verification

- `python3 -m py_compile xoras_startup.py xoras_wake.py` — OK
- Status write smoke (persona_lock_mode present) — OK
- Cargo/vite: not required for Python path; Tauri commands added — run `cargo check` / app rebuild when launching the desktop UI

## Constraints Honored

- Surgical: no L2 memory bridge edits
- Health gates remain fail-closed
- App chat remains fail-open when wake is offline
- Persona lock mode visible in status file and READY chip
