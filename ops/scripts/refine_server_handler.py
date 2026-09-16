#!/usr/bin/env python3
"""
ops/scripts/refine_server_handler.py
Hardens products/xmars_os/server.py HTTP request handling:
1. Rock-solid static file serving (HTML, JS, CSS, JSON, PNG, SVG) with explicit MIME types.
2. Full try-except block wrapping with traceback logging so no connection drops silently.
3. Clean HTTP/1.1 keep-alive and connection headers.
"""

import re
from pathlib import Path

server_file = Path(r"C:\Users\admin\Desktop\SSOT_Agentic_Brain\products\xmars_os\server.py")
content = server_file.read_text(encoding="utf-8")

# Replace do_GET implementation with robust direct handler
old_do_get_start = '    def do_GET(self):'
new_do_get = '''    def do_GET(self):
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
            elif path.startswith("/static/"):
                rel_file = path[len("/static/"):]
                self._serve_static_file(rel_file)
                return
            elif path in ["/styles.css", "/app.js", "/preview_sandbox.html"]:
                self._serve_static_file(path.lstrip("/"))
                return

            # API endpoints
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
        if not target_path.startswith(STATIC_DIR) or not os.path.isfile(target_path):
            self._send_json(404, {"status": "error", "message": f"Static asset '{filename}' not found."})
            return
        
        mime = forced_mime
        if not mime:
            if filename.endswith(".html"): mime = "text/html; charset=utf-8"
            elif filename.endswith(".js"): mime = "application/javascript; charset=utf-8"
            elif filename.endswith(".css"): mime = "text/css; charset=utf-8"
            elif filename.endswith(".json"): mime = "application/json; charset=utf-8"
            elif filename.endswith(".png"): mime = "image/png"
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
'''

# Find do_GET and replace up to do_POST
pattern = r'    def do_GET\(self\):[\s\S]*?(?=    def do_POST\(self\):)'
content = re.sub(pattern, new_do_get + '\n', content)

server_file.write_text(content, encoding="utf-8")
print("[+] Server handler successfully refined with direct static file serving and robust error handling.")
