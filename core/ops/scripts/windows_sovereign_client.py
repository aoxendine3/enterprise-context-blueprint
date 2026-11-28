import json
import urllib.request
import time
from typing import Optional, Dict, Any

class WindowsSovereignNodeClient:
    """
    Hardened client for bare-metal Windows Ollama Node (192.168.1.211).
    Enforces resident model pinning, eliminates thrashing, bounds output tokens,
    and handles fail-closed fallback.
    """
    DEFAULT_HOST = "http://192.168.1.211:11434"
    PINNED_FAST_MODEL = "qwen2.5:0.5b"
    PINNED_NUM_CTX = 4096
    
    def __init__(self, host: str = DEFAULT_HOST, model: str = PINNED_FAST_MODEL):
        self.host = host.rstrip('/')
        self.model = model

    def pin_resident_model(self, keep_alive: str = "24h") -> bool:
        """Warms and pins the target model in host memory with a 24h lease."""
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": "SOVRA_PING_WARM",
            "stream": False,
            "keep_alive": keep_alive,
            "options": {"num_predict": 1, "num_ctx": self.PINNED_NUM_CTX}
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except Exception:
            return False

    def evict_model(self, model_name: str) -> bool:
        """Immediately evicts a secondary model to prevent RAM paging thrash."""
        url = f"{self.host}/api/generate"
        payload = {"model": model_name, "keep_alive": 0}
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def query(self, prompt: str, max_tokens: int = 16, timeout_s: float = 5.0) -> Dict[str, Any]:
        """
        Executes a bounded reasoning pass against the pinned resident model.
        Returns execution latency and raw response.
        """
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "24h",
            "options": {
                "num_predict": max_tokens,
                "num_ctx": self.PINNED_NUM_CTX,
                "temperature": 0.1
            }
        }
        t0 = time.time()
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                elapsed = time.time() - t0
                return {
                    "ok": True,
                    "response": data.get("response", "").strip(),
                    "elapsed_sec": round(elapsed, 4),
                    "model": self.model
                }
        except Exception as e:
            elapsed = time.time() - t0
            return {
                "ok": False,
                "error": str(e),
                "elapsed_sec": round(elapsed, 4),
                "model": self.model
            }
