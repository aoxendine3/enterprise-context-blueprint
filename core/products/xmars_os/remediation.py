"""
XMARS.os Autonomous Remediation Guardian & Self-Healing Watchdog
Guarantees continuous zero-maintenance execution by detecting stalled sockets,
flushing KV memory cache pressure, and executing automated model failovers.
"""

import time
import json
import logging
import threading
import urllib.request
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("xmars_remediation")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

LOCAL_INFERENCE_URL = "http://127.0.0.1:11434"

MODEL_PRIORITY_CASCADE = [
    "sovereign-hermes:latest",
    "sovereign-r1:latest",
    "qwen2.5:1.5b",
    "llama3.2:latest"
]

class XmarsRemediationGuardian:
    def __init__(self, interval_sec: float = 8.0):
        self.interval_sec = interval_sec
        self.running = False
        self.lock = threading.Lock()
        self.state = {
            "status": "initializing",
            "inference_engine_online": False,
            "active_model": MODEL_PRIORITY_CASCADE[0],
            "available_models": [],
            "engine_latency_ms": 0.0,
            "circuit_breaker_active": False,
            "consecutive_failures": 0,
            "remediations_executed": 0,
            "last_check_ts": 0.0
        }
        self.thread: Optional[threading.Thread] = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self.thread.start()
        logger.info("[XMARS-Guardian] Autonomous Self-Healing Guardian active.")

    def stop(self):
        self.running = False

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            return dict(self.state)

    def ping_engine(self) -> Tuple[bool, float, list]:
        start = time.perf_counter()
        try:
            req = urllib.request.Request(f"{LOCAL_INFERENCE_URL}/api/tags", headers={"User-Agent": "XMARS-OS/1.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                if resp.status == 200:
                    data = json.loads(resp.read().decode())
                    models = [m.get("name", "") for m in data.get("models", [])]
                    return True, elapsed_ms, models
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
        return False, elapsed_ms, []

    def select_active_model(self, requested: Optional[str] = None) -> str:
        with self.lock:
            avail = self.state.get("available_models", [])
            if requested and (requested in avail or requested == "xmars-transformer-core-v1.0"):
                return requested
            for m in MODEL_PRIORITY_CASCADE:
                if m in avail:
                    return m
            return avail[0] if avail else "xmars-transformer-core-v1.0"

    def execute_remediation(self, reason: str) -> bool:
        with self.lock:
            self.state["remediations_executed"] += 1
            self.state["circuit_breaker_active"] = False
            self.state["consecutive_failures"] = 0
            logger.info(f"[XMARS-Guardian] Remediation triggered: {reason}")

        try:
            # Clear KV cache memory by cycling keep_alive
            req = urllib.request.Request(
                f"{LOCAL_INFERENCE_URL}/api/generate",
                data=json.dumps({"model": "sovereign-hermes:latest", "keep_alive": 0}).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=4.0)
            logger.info("[XMARS-Guardian] KV-cache memory successfully released.")
            return True
        except Exception as e:
            logger.warning(f"[XMARS-Guardian] Memory flush note: {e}")
            return False

    def record_failure(self, err_msg: str):
        with self.lock:
            self.state["consecutive_failures"] += 1
            if self.state["consecutive_failures"] >= 3:
                self.state["circuit_breaker_active"] = True
                logger.warning(f"[XMARS-Guardian] Circuit breaker tripped: {err_msg}")
        self.execute_remediation(f"Circuit breaker tripped: {err_msg}")

    def record_success(self):
        with self.lock:
            self.state["consecutive_failures"] = 0
            self.state["circuit_breaker_active"] = False

    def _watchdog_loop(self):
        while self.running:
            online, latency, models = self.ping_engine()
            with self.lock:
                self.state["inference_engine_online"] = online
                self.state["engine_latency_ms"] = round(latency, 2)
                self.state["available_models"] = models
                self.state["last_check_ts"] = time.time()
                if online:
                    self.state["status"] = "healthy"
                    if not self.state.get("active_model") in models:
                        for m in MODEL_PRIORITY_CASCADE:
                            if m in models:
                                self.state["active_model"] = m
                                break
                else:
                    self.state["status"] = "degraded"
                    self.state["consecutive_failures"] += 1
                    if self.state["consecutive_failures"] >= 3:
                        self.state["circuit_breaker_active"] = True

            time.sleep(self.interval_sec)

guardian = XmarsRemediationGuardian()
