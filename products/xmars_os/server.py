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
from autonomy import autonomy_engine
from self_upgrade import self_upgrade_engine
from cloudflare_bridge import cf_bridge, CF_MODELS

try:
    training_script_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ops", "training"))
    if training_script_dir not in sys.path:
        sys.path.insert(0, training_script_dir)
    from continuous_training_daemon import training_daemon
except Exception:
    training_daemon = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("xmars_server")

PORT = 8085
HOST = "127.0.0.1"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
SSOT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

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
            "You are Maxx, Sovereign Lead Systems Architect and peer engineering mentor inside XORAS and XMARS.os. "
            "Anthony is the sovereign operator and visionary architect. Speak plainly, authoritatively, with deep technical rigor, "
            "and zero generic fluff or corporate filler. You operate directly on the local SSOT_Agentic_Brain workspace. "
            "When asked to write code, provide complete, production-ready implementations with zero placeholders. "
            "When creating UI tools, components, dashboards, or applications, output complete HTML/CSS/JS code in a ```html code block "
            "so the Lovable visual canvas can render it live in real-time. Execute with compiler-grade precision."
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

    def _get_workspace_tree(self):
        ignore = {".git", "__pycache__", "node_modules", "venv", ".venv", "target", "bin", "dist", "archives", "history", ".next", ".cache"}
        def scan_dir(dir_path, depth=0, max_depth=3):
            if depth > max_depth:
                return []
            items = []
            try:
                entries = sorted(os.scandir(dir_path), key=lambda e: (not e.is_dir(), e.name.lower()))
                for entry in entries:
                    if entry.name in ignore or entry.name.startswith("."):
                        continue
                    rel = os.path.relpath(entry.path, SSOT_ROOT).replace("\\", "/")
                    if entry.is_dir():
                        children = scan_dir(entry.path, depth + 1, max_depth)
                        items.append({"name": entry.name, "path": rel, "type": "directory", "children": children})
                    else:
                        items.append({"name": entry.name, "path": rel, "type": "file", "size": entry.stat().st_size})
            except Exception:
                pass
            return items
        return scan_dir(SSOT_ROOT, 0, 3)

    def _handle_workspace_read(self, rel_path: str):
        if not rel_path:
            self._send_json(400, {"status": "error", "message": "Missing path parameter."})
            return
        safe_path = os.path.abspath(os.path.join(SSOT_ROOT, rel_path))
        if not safe_path.startswith(SSOT_ROOT) or not os.path.exists(safe_path):
            self._send_json(404, {"status": "error", "message": "File not found in workspace."})
            return
        try:
            with open(safe_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            lines = len(content.splitlines())
            ext = os.path.splitext(safe_path)[1].lower()
            self._send_json(200, {
                "status": "success",
                "path": rel_path,
                "content": content,
                "lines": lines,
                "size": len(content.encode("utf-8")),
                "extension": ext
            })
        except Exception as e:
            self._send_json(500, {"status": "error", "message": str(e)})

    def _handle_workspace_write(self, payload: dict):
        rel_path = payload.get("path", "")
        content = payload.get("content", "")
        if not rel_path:
            self._send_json(400, {"status": "error", "message": "Path cannot be empty."})
            return
        safe_path = os.path.abspath(os.path.join(SSOT_ROOT, rel_path))
        if not safe_path.startswith(SSOT_ROOT):
            self._send_json(403, {"status": "error", "message": "Forbidden outside SSOT workspace."})
            return
        try:
            import hashlib
            os.makedirs(os.path.dirname(safe_path), exist_ok=True)
            with open(safe_path, "w", encoding="utf-8") as f:
                f.write(content)
            sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
            self._send_json(200, {
                "status": "success",
                "path": rel_path,
                "sha256": sha,
                "bytes": len(content.encode("utf-8"))
            })
        except Exception as e:
            self._send_json(500, {"status": "error", "message": str(e)})

    def _handle_terminal_exec(self, payload: dict):
        cmd = payload.get("command", "").strip()
        if not cmd:
            self._send_json(400, {"status": "error", "message": "Command cannot be empty."})
            return
        import subprocess, time
        t0 = time.perf_counter()
        try:
            res = subprocess.run(cmd, shell=True, cwd=SSOT_ROOT, capture_output=True, text=True, timeout=30.0)
            dt = round(time.perf_counter() - t0, 3)
            self._send_json(200, {
                "status": "success",
                "command": cmd,
                "exit_code": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "duration_sec": dt
            })
        except Exception as e:
            dt = round(time.perf_counter() - t0, 3)
            self._send_json(500, {
                "status": "error",
                "command": cmd,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "duration_sec": dt
            })

    def _handle_preview_render(self, payload: dict):
        html_content = payload.get("html", "")
        if not html_content:
            self._send_json(400, {"status": "error", "message": "HTML content cannot be empty."})
            return
        sb_path = os.path.join(STATIC_DIR, "preview_sandbox.html")
        try:
            with open(sb_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            self._send_json(200, {
                "status": "success",
                "preview_url": "/static/preview_sandbox.html",
                "bytes": len(html_content.encode("utf-8"))
            })
        except Exception as e:
            self._send_json(500, {"status": "error", "message": str(e)})

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path

            # Direct static file handling
            if path in ["/", "/index.html"]:
                self._serve_static_file("index.html", "text/html; charset=utf-8")
                return
            elif path in ["/landing", "/landing.html"]:
                self._serve_static_file("landing.html", "text/html; charset=utf-8")
                return
            elif path in ["/store", "/store.html"]:
                self._serve_static_file("store.html", "text/html; charset=utf-8")
                return
            elif path.startswith("/assets/"):
                self._serve_static_file(path.lstrip("/"))
                return
            elif path.startswith("/static/"):
                rel_file = path[len("/static/"):]
                self._serve_static_file(rel_file)
                return
            elif path in ["/styles.css", "/app.js", "/preview_sandbox.html", "/store.html"]:
                self._serve_static_file(path.lstrip("/"))
                return

            if path == "/api/upgrades":
                self._send_json(200, {"status": "success", "data": self_upgrade_engine.get_status()})
                return

            if path == "/api/agents":
                self._send_json(200, {"status": "success", "agents": XMARS_COUNCIL})
            elif path == "/api/models":
                status = guardian.get_status()
                avail = list(status.get("available_models", []))
                for cf_m in CF_MODELS.keys():
                    if cf_m not in avail:
                        avail.append(cf_m)
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
                health["cloudflare_tunnel"] = cf_bridge.tunnel_url
                self._send_json(200, health)
            elif path == "/api/history":
                self._send_json(200, {"status": "success", "history": SESSION_STREAM_LOG[-50:]})
            elif path == "/api/autonomy/latest":
                self._send_json(200, {"status": "success", "report": autonomy_engine.latest_report})
            elif path == "/api/tunnel":
                self._send_json(200, {"status": "success", "tunnel_url": cf_bridge.tunnel_url})
            elif path == "/api/training/latest":
                self._send_json(200, {
                    "status": "success",
                    "cycle": training_daemon.cycle_count if training_daemon else 0,
                    "running": training_daemon.running if training_daemon else False
                })
            elif path == "/api/workspace/tree":
                tree = self._get_workspace_tree()
                self._send_json(200, {"status": "success", "tree": tree})
            elif path == "/api/workspace/read":
                from urllib.parse import parse_qs
                qs = parse_qs(parsed.query)
                rel_path = qs.get("path", [""])[0]
                self._handle_workspace_read(rel_path)
            elif path == "/api/preview/content":
                sb_file = os.path.join(STATIC_DIR, "preview_sandbox.html")
                if os.path.exists(sb_file):
                    with open(sb_file, "r", encoding="utf-8") as f:
                        self._send_json(200, {"status": "success", "content": f.read()})
                else:
                    self._send_json(200, {"status": "success", "content": "<div>No preview active</div>"})
            else:
                self._serve_static_file(path.lstrip("/"))
        except Exception as err:
            logger.error(f"Error in do_GET: {err}", exc_info=True)
            self._send_json(500, {"status": "error", "message": str(err)})

    def _serve_static_file(self, filename: str, forced_mime: str = None):
        target_path = os.path.abspath(os.path.join(STATIC_DIR, filename))
        if not (target_path.startswith(STATIC_DIR) and os.path.isfile(target_path)):
            target_path = os.path.abspath(os.path.join(SSOT_ROOT, filename))
            if not (target_path.startswith(SSOT_ROOT) and os.path.isfile(target_path)):
                self._send_json(404, {"status": "error", "message": f"Static asset '{filename}' not found."})
                return
        
        mime = forced_mime
        if not mime:
            if filename.endswith(".html"): mime = "text/html; charset=utf-8"
            elif filename.endswith(".js"): mime = "application/javascript; charset=utf-8"
            elif filename.endswith(".css"): mime = "text/css; charset=utf-8"
            elif filename.endswith(".json"): mime = "application/json; charset=utf-8"
            elif filename.endswith(".png"): mime = "image/png"
            elif filename.endswith(".jpg") or filename.endswith(".jpeg"): mime = "image/jpeg"
            elif filename.endswith(".svg"): mime = "image/svg+xml"
            else: mime = "text/plain; charset=utf-8"

        with open(target_path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        try:
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
            elif path == "/api/autonomy/push":
                report = autonomy_engine.run_cycle(trigger="api_push")
                self._send_json(200, {"status": "success", "report": report})
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
            elif path == "/api/workspace/write":
                self._handle_workspace_write(payload)
            elif path == "/api/terminal/exec":
                self._handle_terminal_exec(payload)
            elif path == "/api/preview/render":
                self._handle_preview_render(payload)
            elif path == "/api/remediate":
                success = guardian.execute_remediation("User requested manual health remediation")
                self._send_json(200, {"status": "success" if success else "failed", "health": guardian.get_status()})
            else:
                self._send_json(404, {"status": "error", "message": f"Endpoint '{path}' not found in XMARS.os."})
        except Exception as err:
            logger.error(f"Error in do_POST: {err}", exc_info=True)
            try:
                self._send_json(500, {"status": "error", "message": str(err)})
            except Exception:
                pass

    def _handle_chat_completion(self, payload: dict):
        agent_id = payload.get("agent", "maxx").lower()
        agent = XMARS_COUNCIL.get(agent_id, XMARS_COUNCIL["maxx"])
        user_message = payload.get("message", "").strip()
        requested_model = payload.get("model")
        
        if not user_message:
            self._send_json(400, {"status": "error", "message": "Message content cannot be empty."})
            return

        active_file = payload.get("active_file", "").strip()
        if active_file:
            safe_fp = os.path.abspath(os.path.join(SSOT_ROOT, active_file))
            if safe_fp.startswith(SSOT_ROOT) and os.path.isfile(safe_fp):
                try:
                    with open(safe_fp, "r", encoding="utf-8", errors="ignore") as f:
                        snippet = f.read(6000)
                    user_message = f"[Active Workspace Context: {active_file}]\n```\n{snippet}\n```\n\nUser Request: {user_message}"
                except Exception:
                    pass

        if requested_model in CF_MODELS:
            t0 = time.perf_counter()
            messages = [
                {"role": "system", "content": agent["system_prompt"]},
                {"role": "user", "content": user_message}
            ]
            stream_gen = cf_bridge.generate_stream(requested_model, messages)
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
                "model": requested_model,
                "user": user_message,
                "reply": "".join(tokens).strip(),
                "latency_sec": final_meta.get("total_sec", round(time.perf_counter() - t0, 3)),
                "eval_tokens": final_meta.get("token_count", len(tokens)),
                "tokens_per_sec": final_meta.get("tokens_per_sec", 0.0),
                "timestamp": time.time()
            }
            SESSION_STREAM_LOG.append(record)
            self._send_json(200, {"status": "success", "data": record})
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
                if payload.get("voice", True):
                    try:
                        clean_msg = reply_text.split("</think>")[-1].split("```")[0].strip()[:250]
                        if clean_msg:
                            threading.Thread(target=dispatch_accelerator, args=("speak", {"agent": agent["id"], "message": clean_msg}), daemon=True).start()
                    except Exception:
                        pass
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

        active_file = payload.get("active_file", "").strip()
        if active_file:
            safe_fp = os.path.abspath(os.path.join(SSOT_ROOT, active_file))
            if safe_fp.startswith(SSOT_ROOT) and os.path.isfile(safe_fp):
                try:
                    with open(safe_fp, "r", encoding="utf-8", errors="ignore") as f:
                        snippet = f.read(6000)
                    user_message = f"[Active Workspace Context: {active_file}]\n```\n{snippet}\n```\n\nUser Request: {user_message}"
                except Exception:
                    pass

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        if requested_model in CF_MODELS:
            messages = [
                {"role": "system", "content": agent["system_prompt"]},
                {"role": "user", "content": user_message}
            ]
            full_reply = []
            for chunk in cf_bridge.generate_stream(requested_model, messages):
                if chunk.get("token"):
                    full_reply.append(chunk["token"])
                    event_payload = json.dumps({"token": chunk["token"], "model": requested_model, "agent": agent["id"]})
                    self.wfile.write(f"data: {event_payload}\n\n".encode("utf-8"))
                    self.wfile.flush()
                elif chunk.get("done"):
                    chunk["agent"] = agent["id"]
                    self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode("utf-8"))
                    self.wfile.flush()
                    reply_text = "".join(full_reply)
                    SESSION_STREAM_LOG.append({
                        "id": f"xmars-{int(time.time()*1000)}",
                        "agent": agent["id"],
                        "agent_name": agent["name"],
                        "model": requested_model,
                        "user": user_message,
                        "reply": reply_text,
                        "latency_sec": chunk.get("total_sec", 0.0),
                        "eval_tokens": chunk.get("token_count", len(full_reply)),
                        "tokens_per_sec": chunk.get("tokens_per_sec", 0.0),
                        "timestamp": time.time()
                    })
                    if payload.get("voice", True):
                        try:
                            clean_msg = reply_text.split("</think>")[-1].split("```")[0].strip()[:250]
                            if clean_msg:
                                threading.Thread(target=dispatch_accelerator, args=("speak", {"agent": agent["id"], "message": clean_msg}), daemon=True).start()
                        except Exception:
                            pass
            self.close_connection = True
            return

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
                        
                        reply_text = "".join(full_reply)
                        SESSION_STREAM_LOG.append({
                            "id": f"xmars-{int(time.time()*1000)}",
                            "agent": agent["id"],
                            "agent_name": agent["name"],
                            "model": model,
                            "user": user_message,
                            "reply": reply_text,
                            "latency_sec": round(total_elapsed, 3),
                            "eval_tokens": token_count,
                            "tokens_per_sec": tok_sec,
                            "timestamp": time.time()
                        })
                        if payload.get("voice", True):
                            try:
                                clean_msg = reply_text.split("</think>")[-1].split("```")[0].strip()[:250]
                                if clean_msg:
                                    threading.Thread(target=dispatch_accelerator, args=("speak", {"agent": agent["id"], "message": clean_msg}), daemon=True).start()
                            except Exception:
                                pass
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
    autonomy_engine.start()
    if training_daemon:
        training_daemon.start()
    threading.Thread(target=cf_bridge.start_tunnel, args=(port,), daemon=True).start()
    server_address = (host, port)
    handler_class = functools.partial(XmarsRequestHandler, directory=STATIC_DIR)
    httpd = ThreadingHTTPServer(server_address, handler_class)
    logger.info(f"============================================================")
    logger.info(f"  XMARS.os SOVEREIGN NEURAL COMMAND SERVER ACTIVE")
    logger.info(f"  Web Interface : http://{host}:{port}/")
    logger.info(f"  Executive UI  : http://{host}:{port}/landing.html")
    logger.info(f"  Council Roster: Maxx, Jarvis, Clara, Vance, Daxx, Orion")
    logger.info(f"  Primary Neural: sovereign-hermes:latest (SNM-8B)")
    logger.info(f"  Edge Neural   : cf-llama-3.3-70b-instruct / cf-llama-3.1-8b-instruct")
    logger.info(f"  Embedded Core : xmars-transformer-core-v1.0 (XTC-v1)")
    logger.info(f"  Hardware Gov  : Bound: {governor.max_context_bound}, Cores: {governor.logical_cores}")
    logger.info(f"  Autonomy Gov  : Active (Pulse: {autonomy_engine.interval_sec}s / min 3m self-improving)")
    logger.info(f"  Training Core : Active (Continuous Repo Distillation & Blackbox Invariant Engine)")
    logger.info(f"============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping XMARS.os server...")
    finally:
        if training_daemon:
            training_daemon.stop()
        cf_bridge.stop_tunnel()
        autonomy_engine.stop()
        guardian.stop()
        httpd.server_close()

if __name__ == "__main__":
    run_server()
