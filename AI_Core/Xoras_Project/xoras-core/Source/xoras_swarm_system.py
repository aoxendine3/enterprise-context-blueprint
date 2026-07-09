"""
xoras_swarm_system.py
Zordax Systems — 5-Layer Swarm Intelligence Architecture Entry Point

Orchestration Details:
  - Supervises all system components in a 3-tier pyramid.
  - Sentinel Watchdog runs in an isolated, auto-recovering background session.
  - Automatically restarts Swarm Governor or Evolution Daemon on crash.
  - Orchestrates Meta Orchestrator dynamic compilation requests.

Author: Zordax Systems / Maxx
Standard: If you can see improvements, it is not done.
"""

from __future__ import annotations

import os
import sys
import time
import json
import signal
import subprocess
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure source folder is in Python path
SOURCE_DIR = Path(__file__).parent
sys.path.insert(0, str(SOURCE_DIR))

from xoras_vector_db import initialize_db
from xoras_meta_orchestrator import XorasMetaOrchestrator

# Configuration
SYSTEM_STATE_PATH = Path("/tmp/xoras_swarm_system.json")
SENTINEL_LOG_PATH = Path("/tmp/sentinel_recovery.log")

# Setup Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("XorasSwarmSystem")

SYSTEM_PID_FILE = Path("/tmp/xoras_swarm_system.pid")

def acquire_system_lock_or_exit():
    if SYSTEM_PID_FILE.exists():
        try:
            pid = int(SYSTEM_PID_FILE.read_text().strip())
            if is_process_alive(pid):
                logger.error(f"[SYSTEM] Swarm System already running under PID {pid}. Exiting.")
                sys.exit(0)
        except (ValueError, OSError):
            pass
    SYSTEM_PID_FILE.write_text(str(os.getpid()))

def release_system_lock():
    try:
        if SYSTEM_PID_FILE.exists():
            os.remove(SYSTEM_PID_FILE)
    except OSError:
        pass


# ─── Process Utilities ────────────────────────────────────────────────────────

def is_process_alive(pid: int) -> bool:
    """Checks if a process is active under the given PID and not a macOS zombie (Z)."""
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    
    # Verify it is not a zombie
    try:
        state = subprocess.check_output(
            ["ps", "-p", str(pid), "-o", "state="], 
            stderr=subprocess.DEVNULL
        ).decode().strip()
        return "Z" not in state and state != ""
    except Exception:
        return False


# ─── Atomic State File I/O ───────────────────────────────────────────────────

def write_system_state(state: Dict[str, Any]) -> None:
    """Atomically writes system state to temp file then renames to target."""
    tmp = SYSTEM_STATE_PATH.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(state, indent=2))
        os.replace(tmp, SYSTEM_STATE_PATH)
    except Exception as e:
        logger.error(f"Failed to write system state: {e}")


def read_system_state() -> Optional[Dict[str, Any]]:
    """Reads system state file safely."""
    if not SYSTEM_STATE_PATH.exists():
        return None
    try:
        return json.loads(SYSTEM_STATE_PATH.read_text())
    except Exception as e:
        logger.error(f"Failed to read system state: {e}")
        return None


# ─── Sentinel Watchdog Loop ───────────────────────────────────────────────────

def run_sentinel_watchdog() -> None:
    """
    Subprocess loop: regularly polls Governor and Evolution Daemon PIDs.
    Restores failed processes, updates system state, and logs recovery times.
    """
    # Redirect sentinel output to log file
    log_file = open(SENTINEL_LOG_PATH, "a", encoding="utf-8")
    sys.stdout = log_file
    sys.stderr = log_file

    print(f"\n[{time.asctime()}] [SENTINEL] Active. Watchdog PID: {os.getpid()}")
    log_file.flush()

    while True:
        time.sleep(0.1)  # 100ms polling latency

        state = read_system_state()
        if not state or state.get("status") == "SHUTDOWN":
            continue

        governor_pid = state.get("governor_pid")
        daemon_pid = state.get("daemon_pid")
        needs_write = False

        # 1. Audit Swarm Governor
        if governor_pid and not is_process_alive(governor_pid):
            start_time = time.perf_counter()
            print(f"[{time.asctime()}] [SENTINEL] Alert! Swarm Governor PID {governor_pid} has died. Rebooting...")
            log_file.flush()

            cmd = [sys.executable, "-u", str(SOURCE_DIR / "xoras_swarm_governor.py")]
            gov_log = open("/tmp/governor_recovery.log", "a")
            proc = subprocess.Popen(cmd, stdout=gov_log, stderr=gov_log, start_new_session=True)
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            print(f"[SENTINEL] Swarm Governor successfully restored under PID: {proc.pid} in {elapsed_ms:.2f}ms.")
            log_file.flush()

            state["governor_pid"] = proc.pid
            needs_write = True

        # 2. Audit Evolution Daemon
        if daemon_pid and not is_process_alive(daemon_pid):
            start_time = time.perf_counter()
            print(f"[{time.asctime()}] [SENTINEL] Alert! Evolution Daemon PID {daemon_pid} has died. Rebooting...")
            log_file.flush()

            cmd = [sys.executable, "-u", str(SOURCE_DIR / "xoras_evolution_daemon.py")]
            daemon_log = open("/tmp/daemon_recovery.log", "a")
            proc = subprocess.Popen(cmd, stdout=daemon_log, stderr=daemon_log, start_new_session=True)

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            print(f"[SENTINEL] Evolution Daemon successfully restored under PID: {proc.pid} in {elapsed_ms:.2f}ms.")
            log_file.flush()

            state["daemon_pid"] = proc.pid
            needs_write = True

        if needs_write:
            write_system_state(state)


# ─── Swarm System Manager ─────────────────────────────────────────────────────

class XorasSwarmSystem:
    def __init__(self) -> None:
        self.governor_proc: Optional[subprocess.Popen] = None
        self.daemon_proc: Optional[subprocess.Popen] = None
        self.sentinel_proc: Optional[subprocess.Popen] = None
        self.orchestrator: Optional[XorasMetaOrchestrator] = None

    def start(self) -> None:
        """Starts Level 2 services and Level 1 Sentinel watchdog."""
        acquire_system_lock_or_exit()
        logger.info("[SYSTEM] Initializing Zordax Swarm Systems...")
        initialize_db()

        # Clean up any orphaned processes from prior runs listed in the system state
        old_state = read_system_state()
        if old_state:
            for key in ["governor_pid", "daemon_pid", "system_pid"]:
                pid = old_state.get(key)
                if pid and pid != os.getpid() and is_process_alive(pid):
                    logger.info(f"[SYSTEM] Cleaning up orphaned process {key} with PID {pid}...")
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except Exception:
                        pass

        # 1. Start Swarm Governor
        gov_log = open("/tmp/governor_std.log", "a")
        self.governor_proc = subprocess.Popen(
            [sys.executable, "-u", str(SOURCE_DIR / "xoras_swarm_governor.py")],
            stdout=gov_log,
            stderr=gov_log,
            start_new_session=True
        )
        logger.info(f"[SYSTEM] Swarm Governor started [PID={self.governor_proc.pid}]")

        # 2. Start Evolution Daemon
        daemon_log = open("/tmp/daemon_std.log", "a")
        self.daemon_proc = subprocess.Popen(
            [sys.executable, "-u", str(SOURCE_DIR / "xoras_evolution_daemon.py")],
            stdout=daemon_log,
            stderr=daemon_log,
            start_new_session=True
        )
        logger.info(f"[SYSTEM] Evolution Daemon started [PID={self.daemon_proc.pid}]")

        # 3. Write PIDs to Atomic System State File
        state = {
            "status": "RUNNING",
            "governor_pid": self.governor_proc.pid,
            "daemon_pid": self.daemon_proc.pid,
            "system_pid": os.getpid(),
            "timestamp": time.time()
        }
        write_system_state(state)

        # 4. Launch Sentinel Watchdog Process
        self.sentinel_proc = subprocess.Popen(
            [sys.executable, "-u", __file__, "--sentinel-watchdog"],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logger.info(f"[SYSTEM] Sentinel Watchdog daemonized [PID={self.sentinel_proc.pid}]")

        # 5. Initialize Meta Orchestrator
        self.orchestrator = XorasMetaOrchestrator(use_governor=True)

    async def execute_task(self, task: str, workspace: str = "system_swarm_workspace") -> str:
        """Dispatches goal execution through dynamic orchestrator layers."""
        if not self.orchestrator:
            raise RuntimeError("Swarm System is not started.")
        logger.info(f"[SYSTEM] Routing high-level goal to Meta-Orchestration: '{task}'")
        return await self.orchestrator.execute_swarm(task, shared_workspace=workspace)

    def shutdown(self) -> None:
        """Gracefully halts all system layers, stopping sentinel supervision first."""
        logger.info("[SYSTEM] Initiating Graceful Swarm System shutdown...")
        
        # Write shutdown state to avoid Sentinel restarting killed children
        state = read_system_state() or {}
        state["status"] = "SHUTDOWN"
        write_system_state(state)

        # 1. Stop Sentinel watchdog
        if self.sentinel_proc:
            try:
                self.sentinel_proc.terminate()
                self.sentinel_proc.wait(timeout=2)
            except Exception:
                pass
            logger.info("[SYSTEM] Sentinel watchdog terminated.")

        # 2. Stop Governor
        if self.governor_proc:
            try:
                self.governor_proc.terminate()
                self.governor_proc.wait(timeout=2)
            except Exception:
                pass
            logger.info("[SYSTEM] Swarm Governor terminated.")

        # 3. Stop Evolution Daemon
        if self.daemon_proc:
            try:
                self.daemon_proc.terminate()
                self.daemon_proc.wait(timeout=2)
            except Exception:
                pass
            logger.info("[SYSTEM] Evolution Daemon terminated.")

        # 4. Cleanup orchestrator compiler
        if self.orchestrator:
            self.orchestrator.cleanup()

        # Clean state files
        try:
            if SYSTEM_STATE_PATH.exists():
                os.remove(SYSTEM_STATE_PATH)
        except OSError:
            pass
        
        release_system_lock()
        logger.info("[SYSTEM] Shutdown complete.")


# ─── CLI Entrypoint ──────────────────────────────────────────────────────────

async def run_main():
    system = XorasSwarmSystem()
    system.start()
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--dispatch":
            task_prompt = sys.argv[2] if len(sys.argv) > 2 else "Perform a full system audit."
            try:
                report = await system.execute_task(task_prompt)
                logger.info("--- SWARM REPORT OUT ---")
                print(report)
            finally:
                system.shutdown()
        else:
            logger.info("[SYSTEM] Swarm running in foreground. Press Ctrl+C to stop.")
            while True:
                await asyncio.sleep(1)
    except asyncio.CancelledError:
        system.shutdown()
    except KeyboardInterrupt:
        system.shutdown()

if __name__ == "__main__":
    if "--sentinel-watchdog" in sys.argv:
        run_sentinel_watchdog()
    else:
        try:
            asyncio.run(run_main())
        except KeyboardInterrupt:
            pass
