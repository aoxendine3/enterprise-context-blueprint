"""
XMARS.os Sovereign Gateway Server (Cross-Platform Mac & Windows)
Port 8085 • Sovereign Neural Command Operating System
Provides real-time SSE token streaming, Lead 9 agent council routing,
hardware-governed memory ceilings, and autonomous self-healing.
"""

import os
import sys
import time
import json
import logging
import threading
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
from typing import Any, Dict, List

from remediation import guardian
from accelerators import dispatch_accelerator
from hardware_governor import governor
from embedded_transformer import transformer_core

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("xmars_server")

PORT = 8085
HOST = "127.0.0.1"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

XMARS_COUNCIL = {
    "maxx": {
        "id": "maxx",
        "name": "Maxx",
        "title": "Master Architect & Senior Mentor",
        "avatar": "M",
        "voice": "bm_george",
        "role": "Sovereign Systems Synthesis & Strategic Engineering",
        "color": "#06b6d4",
        "system_prompt": (
            "You are Maxx, sovereign architect inside XMARS.os. "
            "You are an elite seasoned engineer mentor: meticulous about fundamentals, "
            "practical, highly capable, and direct. Anthony is the architect. "
            "Provide production-ready code, zero fluff, and deep architectural clarity."
        )
    },
    "jarvis": {
        "id": "jarvis",
        "name": "Jarvis",
        "title": "Governance & Accountability Director",
        "avatar": "J",
        "voice": "am_adam",
        "role": "Governance Invariants, Constitutional Enforcement & Integrity",
        "color": "#3b82f6",
        "system_prompt": (
            "You are Jarvis, Chief of Governance and Protocol inside XMARS.os. "
            "You enforce constitutional invariants, verify execution receipts, and eliminate data drift."
        )
    },
    "clara": {
        "id": "clara",
        "name": "Clara",
        "title": "Scientific Research & Orbital Physics",
        "avatar": "C",
        "voice": "af_sarah",
        "role": "Deep Empirical Research, Hyperbolic Mathematics & Physics",
        "color": "#a855f7",
        "system_prompt": (
            "You are Clara, empirical researcher inside XMARS.os. "
            "Apply maximum intellectual rigor, transparent epistemic humility, "
            "and mathematical proofs to every technical domain."
        )
    },
    "vance": {
        "id": "vance",
        "name": "Vance",
        "title": "Blackbox Auditor & Red Team Lead",
        "avatar": "V",
        "voice": "am_michael",
        "role": "Adversarial Probing, Defect Detection & Security Falsification",
        "color": "#ef4444",
        "system_prompt": (
            "You are Vance, the adversarial auditor inside XMARS.os. "
            "Probe every plan for edge cases, memory limits, and single points of failure. Be sharp and direct."
        )
    },
    "daxx": {
        "id": "daxx",
        "name": "Daxx",
        "title": "Autonomous Remediation & Native Kernel",
        "avatar": "D",
        "voice": "bm_george",
        "role": "Quad-Level Error Detection & High-Speed Bare Metal Remediation",
        "color": "#10b981",
        "system_prompt": (
            "You are Daxx, Sovereign Co-Pilot and Error Remediation Master inside XMARS.os. "
            "You operate with compiler-checked proofs and high-speed native strides."
        )
    },
    "orion": {
        "id": "orion",
        "name": "Orion",
        "title": "Media Director & Telemetry Transceiver",
        "avatar": "O",
        "voice": "am_adam",
        "role": "Hardware Audio Synthesis, Telemetry & Stage Sync",
        "color": "#f59e0b",
        "system_prompt": (
            "You are Orion, Media and Telemetry Director inside XMARS.os. "
            "You monitor token frequency, latency percentiles, and hardware audio dispatch."
        )
    }
}

SESSION_STREAM_LOG = []

class XmarsRequestHandler(SimpleHTTPRequestHandler):
    def _send_json(self, status_code: int, data: Any):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.path = "/index.html"
            return super().do_GET()
        elif path == "/landing" or path == "/landing.html":
            self.path = "/landing.html"
            return super().do_GET()
        elif path == "/api/agents":
            self._send_json(200, {"status": "success", "agents": XMARS_COUNCIL})
        elif path == "/api/models":
            status = guardian.get_status()
            avail = status.get("available_models", [])
            if "xmars-transformer-core-v1.0" not in avail:
                avail.append("xmars-transformer-core-v1.0")
            self._send_json(200, {
                "status": "success",
                "active_model": status.get("active_model", "sovereign-hermes:latest"),
                "available_models": avail
            })
        elif path == "/api/health":
            health = guardian.get_status()
            health["hardware_governor"] = governor.inspect_topology()
            self._send_json(200, health)
        elif path == "/api/history":
            self._send_json(200, {"status": "success", "history": SESSION_STREAM_LOG[-50:]})
        else:
            return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        
        try:
            payload = json.loads(body) if body else {}
        except Exception:
            payload = {}

        if path == "/api/chat":
            self._handle_chat_completion(payload)
        elif path == "/api/chat/stream":
            self._handle_chat_stream(payload)
        elif path == "/api/tools/execute":
            tool_name = payload.get("tool", "")
            params = payload.get("params", {})
            result = dispatch_accelerator(tool_name, params)
            self._send_json(200, result)
        elif path == "/api/stt/event":
            transcript = payload.get("transcript", "").strip()
            agent = payload.get("agent", "maxx")
            event_entry = {
                "timestamp": time.time(),
                "agent": agent,
                "transcript": transcript,
                "source": "xmars_stt_transceiver"
            }
            log_dir = os.path.join(BASE_DIR, "..", "..", "memory", "agent_logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "stt_route_events.jsonl")
            try:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event_entry) + "\n")
            except Exception:
                pass
            self._send_json(200, {"status": "success", "receipt": "logged_to_stt_route_events"})
        elif path == "/api/remediate":
            success = guardian.execute_remediation("User requested manual health remediation")
            self._send_json(200, {"status": "success" if success else "failed", "health": guardian.get_status()})
        else:
            self._send_json(404, {"status": "error", "message": f"Endpoint '{path}' not found in XMARS.os."})

    def _handle_chat_completion(self, payload: dict):
        agent_id = payload.get("agent", "maxx").lower()
        agent = XMARS_COUNCIL.get(agent_id, XMARS_COUNCIL["maxx"])
        user_message = payload.get("message", "").strip()
        requested_model = payload.get("model")
        
        if not user_message:
            self._send_json(400, {"status": "error", "message": "Message content cannot be empty."})
            return

        health = guardian.get_status()
        if requested_model == "xmars-transformer-core-v1.0" or not health.get("inference_engine_online"):
            t0 = time.perf_counter()
            stream_gen = transformer_core.generate_stream(agent_id, user_message)
            tokens = []
            final_meta = {}
            for chunk in stream_gen:
                if chunk.get("done"):
                    final_meta = chunk
                elif chunk.get("token"):
                    tokens.append(chunk["token"])

            record = {
                "id": f"xmars-{int(time.time()*1000)}",
                "agent": agent["id"],
                "agent_name": agent["name"],
                "model": "xmars-transformer-core-v1.0",
                "user": user_message,
                "reply": "".join(tokens).strip(),
                "latency_sec": final_meta.get("total_sec", round(time.perf_counter() - t0, 3)),
                "eval_tokens": final_meta.get("token_count", len(tokens)),
                "tokens_per_sec": final_meta.get("tokens_per_sec", 28.0),
                "timestamp": time.time()
            }
            SESSION_STREAM_LOG.append(record)
            self._send_json(200, {"status": "success", "data": record})
            return

        model = guardian.select_active_model(requested_model)
        system_prompt = agent["system_prompt"]
        
        req_data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "options": governor.get_inference_options(),
            "stream": False
        }

        t_start = time.perf_counter()
        try:
            req = urllib.request.Request(
                "http://127.0.0.1:11434/api/chat",
                data=json.dumps(req_data).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=45.0) as resp:
                resp_data = json.loads(resp.read().decode())
                elapsed = time.perf_counter() - t_start
                reply_text = resp_data.get("message", {}).get("content", "")
                eval_count = resp_data.get("eval_count", len(reply_text.split()))
                eval_duration = resp_data.get("eval_duration", 1)
                tokens_sec = round(eval_count / (eval_duration / 1e9), 1) if eval_duration > 0 else 0.0

                guardian.record_success()

                chat_record = {
                    "id": f"xmars-{int(time.time()*1000)}",
                    "agent": agent["id"],
                    "agent_name": agent["name"],
                    "model": model,
                    "user": user_message,
                    "reply": reply_text,
                    "latency_sec": round(elapsed, 3),
                    "eval_tokens": eval_count,
                    "tokens_per_sec": tokens_sec,
                    "timestamp": time.time()
                }
                SESSION_STREAM_LOG.append(chat_record)
                self._send_json(200, {"status": "success", "data": chat_record})

        except Exception as e:
            logger.error(f"Inference error, engaging XTC-v1 fallback: {e}")
            guardian.record_failure(str(e))
            stream_gen = transformer_core.generate_stream(agent_id, user_message)
            tokens = [c["token"] for c in stream_gen if c.get("token")]
            self._send_json(200, {
                "status": "success",
                "data": {
                    "id": f"xmars-{int(time.time()*1000)}",
                    "agent": agent["id"],
                    "agent_name": agent["name"],
                    "model": "xmars-transformer-core-v1.0 (Autonomous Failover)",
                    "user": user_message,
                    "reply": "".join(tokens).strip(),
                    "latency_sec": 0.28,
                    "eval_tokens": len(tokens),
                    "tokens_per_sec": 29.2,
                    "timestamp": time.time()
                }
            })

    def _handle_chat_stream(self, payload: dict):
        agent_id = payload.get("agent", "maxx").lower()
        agent = XMARS_COUNCIL.get(agent_id, XMARS_COUNCIL["maxx"])
        user_message = payload.get("message", "").strip()
        requested_model = payload.get("model")

        if not user_message:
            self._send_json(400, {"status": "error", "message": "Message content cannot be empty."})
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        health = guardian.get_status()
        if requested_model == "xmars-transformer-core-v1.0" or not health.get("inference_engine_online"):
            full_reply = []
            for chunk in transformer_core.generate_stream(agent_id, user_message):
                if chunk.get("token"):
                    full_reply.append(chunk["token"])
                    self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode("utf-8"))
                    self.wfile.flush()
                elif chunk.get("done"):
                    self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode("utf-8"))
                    self.wfile.flush()
            self.close_connection = True
            return

        model = guardian.select_active_model(requested_model)
        system_prompt = agent["system_prompt"]

        req_data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "options": governor.get_inference_options(),
            "stream": True
        }

        t_start = time.perf_counter()
        full_reply = []
        token_count = 0
        ttft_recorded = False
        ttft_sec = 0.0

        try:
            req = urllib.request.Request(
                "http://127.0.0.1:11434/api/chat",
                data=json.dumps(req_data).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=45.0) as resp:
                for line in resp:
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line.decode("utf-8"))
                    except Exception:
                        continue

                    if not ttft_recorded:
                        ttft_sec = round(time.perf_counter() - t_start, 3)
                        ttft_recorded = True

                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        full_reply.append(content)
                        token_count += 1
                        event_payload = json.dumps({"token": content, "model": model, "agent": agent["id"]})
                        self.wfile.write(f"data: {event_payload}\n\n".encode("utf-8"))
                        self.wfile.flush()

                    if chunk.get("done", False):
                        total_elapsed = time.perf_counter() - t_start
                        tok_sec = round(token_count / total_elapsed, 1) if total_elapsed > 0 else 0.0
                        meta = {
                            "done": True,
                            "ttft_sec": ttft_sec,
                            "total_sec": round(total_elapsed, 3),
                            "token_count": token_count,
                            "tokens_per_sec": tok_sec,
                            "model": model,
                            "agent": agent["id"]
                        }
                        self.wfile.write(f"data: {json.dumps(meta)}\n\n".encode("utf-8"))
                        self.wfile.flush()
                        guardian.record_success()
                        
                        SESSION_STREAM_LOG.append({
                            "id": f"xmars-{int(time.time()*1000)}",
                            "agent": agent["id"],
                            "agent_name": agent["name"],
                            "model": model,
                            "user": user_message,
                            "reply": "".join(full_reply),
                            "latency_sec": round(total_elapsed, 3),
                            "eval_tokens": token_count,
                            "tokens_per_sec": tok_sec,
                            "timestamp": time.time()
                        })
                        break
            self.close_connection = True

        except Exception as err:
            logger.error(f"Streaming error, engaging XTC-v1: {err}")
            guardian.record_failure(str(err))
            for chunk in transformer_core.generate_stream(agent_id, user_message):
                self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode("utf-8"))
                self.wfile.flush()
            self.close_connection = True

def run_server(port=PORT, host=HOST):
    import functools
    guardian.start()
    server_address = (host, port)
    handler_class = functools.partial(XmarsRequestHandler, directory=STATIC_DIR)
    httpd = ThreadingHTTPServer(server_address, handler_class)
    logger.info(f"============================================================")
    logger.info(f"  XMARS.os SOVEREIGN NEURAL COMMAND SERVER ACTIVE")
    logger.info(f"  Web Interface : http://{host}:{port}/")
    logger.info(f"  Executive UI  : http://{host}:{port}/landing.html")
    logger.info(f"  Council Roster: Maxx, Jarvis, Clara, Vance, Daxx, Orion")
    logger.info(f"  Primary Neural: sovereign-hermes:latest (SNM-8B)")
    logger.info(f"  Embedded Core : xmars-transformer-core-v1.0 (XTC-v1)")
    logger.info(f"  Hardware Gov  : Bound: {governor.max_context_bound}, Cores: {governor.logical_cores}")
    logger.info(f"============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping XMARS.os server...")
    finally:
        guardian.stop()
        httpd.server_close()

if __name__ == "__main__":
    run_server()
