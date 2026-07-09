#!/Users/ajoxendine68/sovereign/.venv/bin/python3.12
import asyncio
import os
import sys
import subprocess
import sqlite3
import time
import logging
import psutil
import aiohttp
from typing import Dict

logging.basicConfig(
    level=logging.INFO,
    format='[SELF-HEALING] %(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("XorasSelfHealing")


class SelfHealingManager:
    def __init__(
        self,
        data_dir: str | None = None,
    ):
        if data_dir is None:
            data_dir = os.environ.get(
                "XORAS_SOURCE_DIR",
                "/Users/ajoxendine68/Desktop/Xoras_Workspace/AI_Core/Xoras_Project/xoras-core/Source",
            )
        self.data_dir = data_dir
        self.persona_api_url = os.environ.get(
            "XORAS_PERSONA_API", "http://127.0.0.1:8787"
        )
        self.db_paths = {
            "sentinel": os.path.join(data_dir, "sentinel.db"),
            "xoras_memory": os.path.join(data_dir, "xoras_memory.db")
        }
        self.monitored_pids: Dict[str, int] = {}
        self.cpu_history: Dict[str, list] = {}
        self.max_cpu_percent = 80.0
        self.max_memory_bytes = 1.5 * 1024 * 1024 * 1024  # 1.5 GB
        self.ollama_endpoint = "http://192.168.1.133:11434"

    def register_process(self, name: str, pid: int):
        """Registers a process for active telemetry and resource monitoring."""
        self.monitored_pids[name] = pid
        self.cpu_history[name] = []
        logger.info(f"Registered process {name} (PID: {pid}) for monitoring.")

    async def check_database_integrity(self) -> bool:
        """Runs SQLite integrity checks and executes automated repair if corrupted."""
        all_ok = True
        for db_name, db_path in self.db_paths.items():
            if not os.path.exists(db_path):
                continue
            try:
                # Use uri=True to prevent sqlite from automatically creating
                # empty files during a read-only check
                conn = sqlite3.connect(f"file:{db_path}?mode=rw", uri=True)
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check;")
                result = cursor.fetchone()
                conn.close()
                if result and result[0] == "ok":
                    pass
                else:
                    logger.error(
                        f"Database corruption detected in {db_name}.db: {result}")
                    await self._repair_database(db_name, db_path)
                    all_ok = False
            except Exception as e:
                logger.error(f"Failed to check integrity of {db_name}.db: {e}")
                await self._repair_database(db_name, db_path)
                all_ok = False
        return all_ok

    async def _repair_database(self, db_name: str, db_path: str):
        """Executes database healing by backing up corrupted DB

        and recreating schema.
        """
        logger.warning(f"Initiating repair sequence for {db_name}.db...")
        backup_path = f"{db_path}.corrupted_{int(time.time())}"
        try:
            if os.path.exists(db_path):
                os.rename(db_path, backup_path)
                logger.info(f"Corrupted database renamed to {backup_path}")

            # Re-create database schema
            if db_name == "sentinel":
                sys.path.append(self.data_dir)
                import sentinel_core
                sentinel_core.init_db()
                logger.info("Successfully recreated sentinel database schema.")
            elif db_name == "xoras_memory":
                # Re-initialize the Sovereign persistence stores
                sys.path.append(self.data_dir)
                from xoras_sovereign_ai import SovereignBrain
                brain = SovereignBrain()
                await brain.check_health()
                logger.info("Successfully re-initialized xoras_memory database schema.")
        except Exception as repair_err:
            logger.critical(f"Database repair failed for {db_name}.db: {repair_err}")

    async def monitor_resources(self) -> Dict[str, str]:
        """Checks registered processes for CPU/Memory spikes or leaks

        and triggers self-healing.
        """
        actions = {}
        for name, pid in list(self.monitored_pids.items()):
            try:
                proc = psutil.Process(pid)
                if not proc.is_running() or proc.status() == psutil.STATUS_ZOMBIE:
                    logger.warning(
                        f"Process {name} (PID: {pid}) is dead or "
                        "a zombie. Restart required."
                    )
                    actions[name] = "RESTART"
                    continue

                # Telemetry
                cpu = proc.cpu_percent(interval=0.05)
                mem = proc.memory_info().rss

                # Check memory limits (leak protection)
                if mem > self.max_memory_bytes:
                    logger.warning(
                        f"Memory leak detected in {name} (PID: {pid}). "
                        f"Usage: {mem / (1024 * 1024):.2f} MB. "
                        "Exceeds 1.5GB. Killing process."
                    )
                    proc.kill()
                    actions[name] = "RESTART"
                    continue

                # Check CPU runaway limits (cpu spike protection)
                self.cpu_history[name].append(cpu)
                if len(self.cpu_history[name]) > 5:
                    self.cpu_history[name].pop(0)

                if (len(self.cpu_history[name]) == 5 and
                        all(c > self.max_cpu_percent
                            for c in self.cpu_history[name])):
                    logger.warning(
                        f"Runaway CPU detected in {name} (PID: {pid}). "
                        f"CPU usage history: {self.cpu_history[name]}. "
                        "Killing process."
                    )
                    proc.kill()
                    actions[name] = "RESTART"
                    continue

            except psutil.NoSuchProcess:
                logger.warning(
                    f"Process {name} (PID: {pid}) not found. Restart required.")
                actions[name] = "RESTART"
            except Exception as e:
                logger.error(f"Error checking resource telemetry for {name}: {e}")

        return actions

    async def check_ollama_health(self) -> bool:
        """Monitors the local Ollama daemon and restarts it on macOS if offline."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_endpoint}/api/tags") as resp:
                    if resp.status == 200:
                        return True
        except Exception:
            pass

        logger.warning(
            "Ollama daemon is offline. Initiating self-healing restart sequence...")
        try:
            # Attempt to launch Ollama app on macOS
            subprocess.Popen(["open", "-a", "Ollama"])
            # Wait up to 5 seconds for initialization
            for _ in range(5):
                await asyncio.sleep(1)
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"{self.ollama_endpoint}/api/tags"
                        ) as resp:
                            if resp.status == 200:
                                logger.info("Ollama daemon successfully restored.")
                                return True
                except Exception:
                    pass
        except Exception as e:
            logger.critical(f"Failed to restore Ollama daemon: {e}")

        return False

    async def check_persona_api_health(self) -> bool:
        """Verify persona API sidecar on port 8787."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.persona_api_url}/health",
                    timeout=aiohttp.ClientTimeout(total=4),
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def restart_persona_api(self) -> bool:
        """Restart persona API if health check fails."""
        if await self.check_persona_api_health():
            return True
        logger.warning("Persona API offline — restarting xoras_persona_api.py")
        try:
            subprocess.Popen(
                [sys.executable, "xoras_persona_api.py"],
                cwd=self.data_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            await asyncio.sleep(2)
            return await self.check_persona_api_health()
        except Exception as e:
            logger.critical(f"Failed to restart persona API: {e}")
            return False
