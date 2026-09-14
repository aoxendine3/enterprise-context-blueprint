"""
XMARS.os Cloudflare Sovereign Bridge
Manages Cloudflare Workers AI (LLM inference + Whisper STT)
and Zero Trust Cloudflare Tunnels for end-to-end SaaS global distribution.
"""

import os
import sys
import json
import time
import logging
import subprocess
import threading
import urllib.request
import urllib.error
from typing import Dict, Any, Generator, Optional

logger = logging.getLogger("xmars_cloudflare")

CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "eb363bcfe2d366cd79f95aa3efd25f8c")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "cfut_lc6Oky8uBl9ULX4x80X90fI4iLvfnvb9KoBPhhxk61758b8e")

CF_MODELS = {
    "cf-llama-3.3-70b-instruct": "@cf/meta/llama-3.3-70b-instruct",
    "cf-llama-3.1-8b-instruct": "@cf/meta/llama-3.1-8b-instruct"
}

class CloudflareBridge:
    def __init__(self, account_id: str = CLOUDFLARE_ACCOUNT_ID, api_token: str = CLOUDFLARE_API_TOKEN):
        self.account_id = account_id
        self.api_token = api_token
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}"
        self.tunnel_process: Optional[subprocess.Popen] = None
        self.tunnel_url: Optional[str] = None
        self.tunnel_thread: Optional[threading.Thread] = None

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    def verify_credentials(self) -> bool:
        try:
            req = urllib.request.Request(
                "https://api.cloudflare.com/client/v4/user/tokens/verify",
                headers=self._headers()
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
                return data.get("success", False)
        except Exception as e:
            logger.error(f"[CF-Bridge] Credential verification failed: {e}")
            return False

    def generate_stream(self, model_id: str, messages: list) -> Generator[Dict[str, Any], None, None]:
        cf_model = CF_MODELS.get(model_id, "@cf/meta/llama-3.1-8b-instruct")
        url = f"{self.base_url}/ai/run/{cf_model}"
        payload = {
            "messages": messages,
            "stream": True
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=self._headers()
        )
        t0 = time.perf_counter()
        token_count = 0

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                for line in resp:
                    line_str = line.decode("utf-8").strip()
                    if not line_str.startswith("data:"):
                        continue
                    data_str = line_str[5:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        token = chunk.get("response", "")
                        if token:
                            token_count += 1
                            yield {"token": token, "done": False}
                    except Exception:
                        continue
            total_sec = round(time.perf_counter() - t0, 3)
            tok_sec = round(token_count / total_sec, 1) if total_sec > 0 else 0.0
            yield {
                "token": "",
                "done": True,
                "total_sec": total_sec,
                "token_count": token_count,
                "tokens_per_sec": tok_sec,
                "model": model_id
            }
        except Exception as e:
            logger.error(f"[CF-Bridge] Workers AI streaming error: {e}")
            yield {"token": f"\n[Cloudflare Edge Fallback Notice: {e}]", "done": False}
            yield {"token": "", "done": True, "total_sec": 0.1, "token_count": 0, "tokens_per_sec": 0.0, "model": model_id}

    def transcribe_audio(self, audio_bytes: bytes) -> Dict[str, Any]:
        url = f"{self.base_url}/ai/run/@cf/openai/whisper"
        req = urllib.request.Request(
            url,
            data=audio_bytes,
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/octet-stream"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            logger.error(f"[CF-Bridge] Whisper transcription error: {e}")
            return {"error": str(e)}

    def start_tunnel(self, local_port: int = 8085) -> Optional[str]:
        if self.tunnel_url:
            return self.tunnel_url
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cf_bin = os.path.join(base_dir, "bin", "cloudflared.exe")
        if not os.path.exists(cf_bin):
            cf_bin = "cloudflared"

        cmd = [cf_bin, "tunnel", "--url", f"http://127.0.0.1:{local_port}", "--no-autoupdate"]
        logger.info(f"[CF-Tunnel] Spawning Cloudflare Quick Tunnel: {' '.join(cmd)}")

        def _monitor_tunnel():
            import re
            try:
                self.tunnel_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
                for line in self.tunnel_process.stdout:
                    match = url_pattern.search(line)
                    if match and not self.tunnel_url:
                        self.tunnel_url = match.group(0)
                        logger.info(f"============================================================")
                        logger.info(f"  XMARS.os SAAS GLOBAL PUBLIC URL: {self.tunnel_url}")
                        logger.info(f"============================================================")
                        tunnel_file = os.path.join(base_dir, "TUNNEL_URL.txt")
                        with open(tunnel_file, "w", encoding="utf-8") as f:
                            f.write(self.tunnel_url + "\n")
                        log_dir = os.path.join(base_dir, "..", "..", "memory", "agent_logs")
                        os.makedirs(log_dir, exist_ok=True)
                        log_file = os.path.join(log_dir, "xmars_saas_tunnel.json")
                        with open(log_file, "w", encoding="utf-8") as lf:
                            json.dump({"tunnel_url": self.tunnel_url, "created_at": time.time(), "port": local_port}, lf, indent=2)
            except Exception as e:
                logger.error(f"[CF-Tunnel] Error running tunnel: {e}")

        self.tunnel_thread = threading.Thread(target=_monitor_tunnel, name="XmarsTunnelThread", daemon=True)
        self.tunnel_thread.start()

        t0 = time.time()
        while time.time() - t0 < 10 and not self.tunnel_url:
            time.sleep(0.5)

        return self.tunnel_url

    def stop_tunnel(self):
        if self.tunnel_process:
            try:
                self.tunnel_process.terminate()
            except Exception:
                pass
            self.tunnel_process = None
            self.tunnel_url = None

cf_bridge = CloudflareBridge()