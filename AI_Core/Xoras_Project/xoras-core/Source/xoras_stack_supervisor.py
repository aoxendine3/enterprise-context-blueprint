#!/usr/bin/env python3
"""Xoras stack supervisor — self-healing for persona API, dream orchestrator, Ollama."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import pathlib
import subprocess
import sys
import time
from typing import Dict, Optional

import aiohttp

ROOT = pathlib.Path(__file__).resolve().parent
STATUS_FILE = ROOT / ".xoras_stack_status.json"
LOG_FILE = ROOT / "xoras_stack_supervisor.log"

PERSONA_API = os.environ.get("XORAS_PERSONA_API", "http://127.0.0.1:8787")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
CHECK_INTERVAL = int(os.environ.get("XORAS_SUPERVISOR_INTERVAL", "30"))
OLLAMA_AUTO_LAUNCH = os.environ.get("XORAS_OLLAMA_AUTO_LAUNCH", "0").strip() == "1"
_last_ollama_launch: float = 0.0
OLLAMA_LAUNCH_COOLDOWN = int(os.environ.get("XORAS_OLLAMA_LAUNCH_COOLDOWN", "600"))

logging.basicConfig(
    level=logging.INFO,
    format="[STACK-SUPERVISOR] %(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("XorasStackSupervisor")


class StackSupervisor:
    def __init__(self) -> None:
        self.processes: Dict[str, subprocess.Popen] = {}
        self.python = sys.executable

    def _write_status(self, payload: dict) -> None:
        payload["timestamp"] = time.time()
        try:
            STATUS_FILE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        except Exception as exc:
            log.warning("Could not write stack status: %s", exc)

    async def _probe(self, url: str) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                    return resp.status == 200
        except Exception:
            return False

    def _start(self, name: str, script: str) -> None:
        if name in self.processes:
            proc = self.processes[name]
            if proc.poll() is None:
                return
        try:
            proc = subprocess.Popen(
                [self.python, script],
                cwd=str(ROOT),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.processes[name] = proc
            log.info("Started %s (pid=%s)", name, proc.pid)
        except Exception as exc:
            log.error("Failed to start %s: %s", name, exc)

    def _ensure_running(self, name: str, script: str) -> bool:
        proc = self.processes.get(name)
        if proc is not None and proc.poll() is None:
            return True
        log.warning("%s not running — restarting", name)
        self._start(name, script)
        return self.processes.get(name) is not None and self.processes[name].poll() is None

    async def run_cycle(self) -> dict:
        persona_ok = await self._probe(f"{PERSONA_API}/health")
        if not persona_ok:
            self._start("persona_api", "xoras_persona_api.py")
            await asyncio.sleep(2)
            persona_ok = await self._probe(f"{PERSONA_API}/health")

        dream_running = self._ensure_running("dream_orchestrator", "xoras_dream_orchestrator.py")

        ollama_ok = await self._probe(f"{OLLAMA_URL}/api/tags")
        global _last_ollama_launch
        if not ollama_ok and OLLAMA_AUTO_LAUNCH:
            now = time.time()
            if now - _last_ollama_launch >= OLLAMA_LAUNCH_COOLDOWN:
                try:
                    subprocess.Popen(["open", "-a", "Ollama"])
                    _last_ollama_launch = now
                    log.info("Ollama auto-launch (opt-in) via open -a")
                except Exception as exc:
                    log.warning("Ollama auto-launch failed: %s", exc)
        elif not ollama_ok:
            log.debug("Ollama offline at %s (auto-launch disabled)", OLLAMA_URL)

        status = {
            "persona_api": persona_ok,
            "dream_orchestrator": dream_running,
            "ollama": ollama_ok,
            "persona_api_url": PERSONA_API,
        }
        self._write_status(status)
        return status

    async def run_forever(self) -> None:
        log.info("Stack supervisor online (interval=%ss)", CHECK_INTERVAL)
        while True:
            status = await self.run_cycle()
            log.info(
                "Health: persona_api=%s dream=%s ollama=%s",
                status["persona_api"],
                status["dream_orchestrator"],
                status["ollama"],
            )
            await asyncio.sleep(CHECK_INTERVAL)


def main() -> None:
    supervisor = StackSupervisor()
    asyncio.run(supervisor.run_forever())


if __name__ == "__main__":
    main()
