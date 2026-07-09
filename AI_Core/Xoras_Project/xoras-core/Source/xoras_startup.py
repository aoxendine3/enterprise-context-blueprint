#!/usr/bin/env python3
"""Full Xoras startup / wake sequence.

Phases (fail-closed): IDENTITY → MEMORY → SECURITY → SERVICES → READY

Writes live status to Source/.xoras_wake_status.json and mirrors phase markers
to xoras_startup.log. Loud, human-visible banners on stdout.
"""
from __future__ import annotations

import datetime
import json
import os
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent
AGENTS_MANIFEST = ROOT.parent / ".agents" / "AGENTS.md"
WATCHDOG = ROOT / "xoras_memory_leak_detector.py"
DAEMON = ROOT / "xoras_daemon.py"
DASHBOARD = ROOT / "xoras_live_dashboard.py"  # optional
LOGFILE = ROOT / "xoras_startup.log"
STARTUP_LOCK = ROOT / ".xoras_startup.lock"
WAKE_STATUS = ROOT / ".xoras_wake_status.json"

PERSONA_API = os.environ.get("XORAS_PERSONA_API", "http://127.0.0.1:8787")
PERSONA_API_SCRIPT = ROOT / "xoras_persona_api.py"
DREAM_ORCHESTRATOR = ROOT / "xoras_dream_orchestrator.py"
STACK_SUPERVISOR = ROOT / "xoras_stack_supervisor.py"

REQUIRED_HEALTH_ENDPOINTS = [
    f"{PERSONA_API}/health",
]

OPTIONAL_HEALTH_ENDPOINTS = [
    "http://localhost:1420/health",
]

PHASES = ("IDENTITY", "MEMORY", "SECURITY", "SERVICES", "READY")
VALID_LOCK_MODES = {"fixed", "allowlisted", "free"}

BANNER_WIDTH = 62


def _now_iso() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _persona_lock_mode() -> str:
    mode = os.getenv("XORAS_PERSONA_LOCK_MODE", "allowlisted").strip().lower()
    return mode if mode in VALID_LOCK_MODES else "allowlisted"


def _banner(title: str) -> str:
    bar = "=" * BANNER_WIDTH
    pad = max(0, BANNER_WIDTH - 4 - len(title))
    left = pad // 2
    right = pad - left
    return f"\n{bar}\n  {' ' * left}{title}{' ' * right}\n{bar}\n"


def _write_status(
    phase: str,
    status: str,
    message: str,
    *,
    persona_lock_mode: str | None = None,
) -> None:
    payload = {
        "phase": phase,
        "status": status,
        "message": message,
        "timestamp": _now_iso(),
        "pid": os.getpid(),
        "persona_lock_mode": persona_lock_mode if persona_lock_mode is not None else _persona_lock_mode(),
    }
    try:
        WAKE_STATUS.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    except Exception as exc:
        print(f"WARN: could not write wake status file: {exc}", flush=True)


def log(message: str, *, phase: str | None = None) -> None:
    timestamp = _now_iso()
    marker = f"[{phase}] " if phase else ""
    line = f"[{timestamp}] {marker}{message}"
    try:
        with LOGFILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(message, flush=True)


def _phase_start(phase: str, message: str) -> None:
    print(_banner(f"PHASE: {phase}"), flush=True)
    log(f"▶ {phase}: {message}", phase=phase)
    _write_status(phase, "running", message)


def _phase_ok(phase: str, message: str) -> None:
    log(f"✓ {phase}: {message}", phase=phase)
    _write_status(phase, "ok", message)


def _fail(phase: str, message: str) -> None:
    print(_banner("FAILED"), flush=True)
    log(f"✗ FAILED at {phase}: {message}", phase="FAILED")
    _write_status("FAILED", "failed", f"{phase}: {message}")
    print(
        f"\n{'!' * BANNER_WIDTH}\n"
        f"  XORAS WAKE FAILED — phase {phase}\n"
        f"  {message}\n"
        f"{'!' * BANNER_WIDTH}\n",
        flush=True,
    )


def _ready(message: str) -> None:
    lock_mode = _persona_lock_mode()
    print(_banner("READY"), flush=True)
    log(f"✓ READY: {message}", phase="READY")
    _write_status("READY", "ok", message, persona_lock_mode=lock_mode)
    print(
        f"\n{'*' * BANNER_WIDTH}\n"
        f"  XORAS WAKE COMPLETE — READY\n"
        f"  persona_lock_mode={lock_mode}\n"
        f"  {message}\n"
        f"{'*' * BANNER_WIDTH}\n",
        flush=True,
    )


def _acquire_startup_lock() -> bool:
    """Best-effort lock to avoid duplicate startup races."""
    if STARTUP_LOCK.exists():
        try:
            pid = STARTUP_LOCK.read_text(encoding="utf-8").strip()
        except Exception:
            pid = "unknown"
        log(f"ERROR: Startup lock already exists (pid={pid}). Refusing duplicate wake.")
        return False
    try:
        STARTUP_LOCK.write_text(str(os.getpid()), encoding="utf-8")
        return True
    except Exception as exc:
        log(f"ERROR: Could not create startup lock: {exc}")
        return False


def _release_startup_lock() -> None:
    try:
        if STARTUP_LOCK.exists():
            STARTUP_LOCK.unlink()
    except Exception as exc:
        log(f"WARN: Could not release startup lock: {exc}")


def _wait_for_health(url: str, retries: int = 12, delay_s: float = 1.0) -> bool:
    """Poll a health endpoint and fail closed if it never comes up."""
    for attempt in range(1, retries + 1):
        try:
            result = subprocess.run(
                ["curl", "-s", "--max-time", "3", url],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                log(
                    f"Health check passed ({url}) on attempt {attempt}: "
                    f"{result.stdout.strip()}"
                )
                return True
        except Exception as exc:
            log(f"WARN: Health probe exception for {url} on attempt {attempt}: {exc}")
        time.sleep(delay_s)
    log(f"ERROR: Health check failed after {retries} attempts for {url}")
    return False


def run_wake() -> int:
    """Execute the full wake sequence. Returns process exit code."""
    print(_banner("XORAS WAKE SEQUENCE"), flush=True)
    log("XORAS WAKE SEQUENCE initiated.")
    _write_status("IDENTITY", "running", "Wake sequence starting")

    lock_held = _acquire_startup_lock()
    if not lock_held:
        _fail("IDENTITY", "Startup lock already held — refusing duplicate wake")
        return 1

    startup_ok = False
    watchdog_proc = None
    daemon_proc = None
    persona_api_proc = None
    dream_proc = None
    supervisor_proc = None
    fail_phase = "IDENTITY"
    fail_message = "Wake contract gate did not complete."

    try:
        # ── IDENTITY ──────────────────────────────────────────────
        fail_phase = "IDENTITY"
        _phase_start("IDENTITY", "Verifying agents manifest and identity surface")
        if not AGENTS_MANIFEST.is_file():
            fail_message = f"Agents manifest not found at {AGENTS_MANIFEST}"
            _fail("IDENTITY", fail_message)
            return 1
        lock_mode = _persona_lock_mode()
        _phase_ok(
            "IDENTITY",
            f"Manifest verified; persona_lock_mode={lock_mode}",
        )

        # ── MEMORY ────────────────────────────────────────────────
        fail_phase = "MEMORY"
        _phase_start("MEMORY", "Starting memory watchdog")
        if not WATCHDOG.is_file():
            fail_message = "Memory watchdog script not found."
            _fail("MEMORY", fail_message)
            return 1
        watchdog_proc = subprocess.Popen(
            [sys.executable, str(WATCHDOG)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(ROOT),
        )
        time.sleep(0.3)
        if watchdog_proc.poll() is not None:
            fail_message = "Memory watchdog exited immediately after start."
            _fail("MEMORY", fail_message)
            return 1
        _phase_ok("MEMORY", f"Watchdog running (pid={watchdog_proc.pid})")

        # ── SECURITY ──────────────────────────────────────────────
        fail_phase = "SECURITY"
        _phase_start("SECURITY", "Locking persona mode and startup gate")
        if lock_mode not in VALID_LOCK_MODES:
            fail_message = f"Invalid persona_lock_mode={lock_mode!r}"
            _fail("SECURITY", fail_message)
            return 1
        if not STARTUP_LOCK.is_file():
            fail_message = "Startup lock missing during SECURITY phase."
            _fail("SECURITY", fail_message)
            return 1
        _write_status(
            "SECURITY",
            "ok",
            f"Persona lock engaged ({lock_mode}); startup lock held",
            persona_lock_mode=lock_mode,
        )
        log(
            f"✓ SECURITY: persona_lock_mode={lock_mode}; startup lock held",
            phase="SECURITY",
        )

        # ── SERVICES ──────────────────────────────────────────────
        fail_phase = "SERVICES"
        _phase_start("SERVICES", "Launching persona API, dream orchestrator, core daemon, health gates")

        if PERSONA_API_SCRIPT.is_file():
            persona_api_proc = subprocess.Popen(
                [sys.executable, str(PERSONA_API_SCRIPT)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=str(ROOT),
            )
            time.sleep(1)
            log(f"Persona API started (pid={persona_api_proc.pid})", phase="SERVICES")
        else:
            fail_message = f"Persona API script not found at {PERSONA_API_SCRIPT}"
            _fail("SERVICES", fail_message)
            return 1

        if DREAM_ORCHESTRATOR.is_file():
            dream_proc = subprocess.Popen(
                [sys.executable, str(DREAM_ORCHESTRATOR)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=str(ROOT),
            )
            log(f"Dream orchestrator started (pid={dream_proc.pid})", phase="SERVICES")

        if STACK_SUPERVISOR.is_file():
            supervisor_proc = subprocess.Popen(
                [sys.executable, str(STACK_SUPERVISOR)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=str(ROOT),
            )
            log(f"Stack supervisor started (pid={supervisor_proc.pid})", phase="SERVICES")

        if not DAEMON.is_file():
            fail_message = "Core daemon script not found."
            _fail("SERVICES", fail_message)
            return 1
        daemon_proc = subprocess.Popen(
            [sys.executable, str(DAEMON)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(ROOT),
        )
        time.sleep(0.3)
        if daemon_proc.poll() is not None:
            fail_message = "Core daemon exited immediately after start."
            _fail("SERVICES", fail_message)
            return 1
        log(f"Daemon started (pid={daemon_proc.pid})", phase="SERVICES")

        if DASHBOARD.is_file():
            dashboard_proc = subprocess.Popen(
                [sys.executable, str(DASHBOARD)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=str(ROOT),
            )
            log(f"Dashboard launched (pid={dashboard_proc.pid})", phase="SERVICES")
        else:
            log("Dashboard script not found — skipped.", phase="SERVICES")

        if watchdog_proc.poll() is not None:
            fail_message = "Memory watchdog died before health gates."
            _fail("SERVICES", fail_message)
            return 1
        if daemon_proc.poll() is not None:
            fail_message = "Core daemon died before health gates."
            _fail("SERVICES", fail_message)
            return 1

        for endpoint in REQUIRED_HEALTH_ENDPOINTS:
            if not _wait_for_health(endpoint):
                fail_message = f"Health gate failed (fail-closed): {endpoint}"
                _fail("SERVICES", fail_message)
                return 1

        for endpoint in OPTIONAL_HEALTH_ENDPOINTS:
            if not _wait_for_health(endpoint, retries=3, delay_s=0.5):
                log(f"Optional health gate offline (continuing): {endpoint}", phase="SERVICES")

        _phase_ok("SERVICES", "Core services up; required health gates passed")

        # ── READY ─────────────────────────────────────────────────
        fail_phase = "READY"
        startup_ok = True
        _ready("Startup completed; all required health gates passed.")
        return 0

    except SystemExit as exc:
        code = int(exc.code) if isinstance(exc.code, int) else 1
        if code != 0 and not startup_ok:
            _fail(fail_phase, fail_message)
        return code if code != 0 else 1
    except Exception as exc:
        fail_message = f"Unhandled wake error: {exc}"
        _fail(fail_phase, fail_message)
        return 1
    finally:
        if not startup_ok:
            # Ensure FAILED status is present even if an early path skipped _fail
            try:
                if WAKE_STATUS.is_file():
                    current = json.loads(WAKE_STATUS.read_text(encoding="utf-8"))
                    if current.get("phase") != "FAILED" and current.get("status") != "failed":
                        _write_status("FAILED", "failed", fail_message)
                else:
                    _write_status("FAILED", "failed", fail_message)
            except Exception:
                _write_status("FAILED", "failed", fail_message)
            log("ERROR: Startup failed. Wake contract gate did not complete.")
        if lock_held:
            _release_startup_lock()


def main() -> None:
    sys.exit(run_wake())


if __name__ == "__main__":
    main()
