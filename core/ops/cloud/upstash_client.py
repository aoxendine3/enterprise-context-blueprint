#!/usr/bin/env python3
"""
===============================================================================
XORAS::OS - UPSTASH SERVERLESS REDIS & QSTASH QUEUE CLIENT (v1.0.0)
===============================================================================
Mandate: Serverless State Store & Async Agent Job Publishing with Retries
Author: The Lead 9 Council (Maxx, Clara, Vance, John, DAXX)
===============================================================================
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import hashlib
from typing import Dict, Any, List, Optional

CREDENTIALS_FILE = os.path.expanduser("~/Desktop/SSOT_Agentic_Brain/.sovereign/credentials.json")

class SovereignUpstashClient:
    def __init__(self):
        self.redis_url, self.redis_token, self.qstash_token = self._load_credentials()

    def _load_credentials(self) -> (str, str, str):
        redis_url = os.environ.get("UPSTASH_REDIS_REST_URL", "https://xoras-redis.upstash.io")
        redis_token = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")
        qstash_token = os.environ.get("QSTASH_TOKEN", "")
        if os.path.exists(CREDENTIALS_FILE):
            try:
                with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                    creds = json.load(f)
                    u_cfg = creds.get("credentials", {}).get("upstash", {})
                    redis_url = u_cfg.get("redis_url", redis_url)
                    if not redis_token:
                        redis_token = u_cfg.get("redis_token", "")
                    if not qstash_token:
                        qstash_token = u_cfg.get("qstash_token", "")
            except Exception:
                pass
        return redis_url, redis_token, qstash_token

    def redis_set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> Dict[str, Any]:
        """
        Sets a key-value pair in Upstash Serverless Redis.
        """
        url = f"{self.redis_url.rstrip('/')}/set/{urllib.parse.quote(key)}"
        if ttl_seconds:
            url += f"?EX={ttl_seconds}"

        payload = json.dumps(value).encode("utf-8") if not isinstance(value, str) else value.encode("utf-8")
        headers = {"Authorization": f"Bearer {self.redis_token}"} if self.redis_token else {}

        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return {"status": "success", "result": data.get("result"), "offline_mock": False}
        except Exception as e:
            return {"status": "offline_airgap_mode", "key": key, "value": value, "error": str(e), "offline_mock": True}

    def redis_get(self, key: str) -> Dict[str, Any]:
        """
        Gets a key-value pair from Upstash Serverless Redis.
        """
        url = f"{self.redis_url.rstrip('/')}/get/{urllib.parse.quote(key)}"
        headers = {"Authorization": f"Bearer {self.redis_token}"} if self.redis_token else {}

        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return {"status": "success", "value": data.get("result"), "offline_mock": False}
        except Exception as e:
            return {"status": "offline_airgap_mode", "key": key, "value": f"mock_value_for_{key}", "error": str(e), "offline_mock": True}

    def qstash_publish_job(self, destination_url: str, message: Dict[str, Any], delay_seconds: int = 0) -> Dict[str, Any]:
        """
        Publishes an async job message to QStash queue with automated retries.
        """
        url = f"https://qstash.upstash.io/v2/publish/{destination_url}"
        headers = {
            "Authorization": f"Bearer {self.qstash_token}",
            "Content-Type": "application/json"
        }
        if delay_seconds > 0:
            headers["Upstash-Delay"] = f"{delay_seconds}s"

        payload = json.dumps(message).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return {"status": "success", "message_id": data.get("messageId"), "offline_mock": False}
        except Exception as e:
            msg_id = f"msg_mock_{hashlib.sha256(payload).hexdigest()[:12]}"
            return {"status": "offline_airgap_mode", "message_id": msg_id, "destination": destination_url, "error": str(e), "offline_mock": True}

if __name__ == "__main__":
    upstash = SovereignUpstashClient()
    print("=================================================================")
    print("  XORAS::OS - UPSTASH REDIS & QSTASH CLIENT TEST")
    print("=================================================================")
    set_res = upstash.redis_set("xoras_state_node_001", {"status": "ACTIVE", "rank": 100})
    print(f"[+] Redis SET Status: {set_res['status']} (Offline Mode: {set_res['offline_mock']})")

    job_res = upstash.qstash_publish_job("https://agent.xoras.io/webhook", {"task": "AUDIT_SWARM_NODES"})
    print(f"[+] QStash Publish Status: {job_res['status']} (MsgID: {job_res.get('message_id')})")
    print("=================================================================")
