#!/usr/bin/env python3
"""
ops/scripts/update_server_endpoints.py
Injects Cursor workspace file explorer, terminal execution, Lovable preview,
and enhanced Hermes cognitive prompts into products/xmars_os/server.py.
"""

import re
from pathlib import Path

server_file = Path(r"C:\Users\admin\Desktop\SSOT_Agentic_Brain\products\xmars_os\server.py")
content = server_file.read_text(encoding="utf-8")

# Ensure SSOT_ROOT is defined
if "SSOT_ROOT =" not in content:
    content = content.replace(
        'STATIC_DIR = os.path.join(BASE_DIR, "static")',
        'STATIC_DIR = os.path.join(BASE_DIR, "static")\nSSOT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))'
    )

# Enrich Maxx's system prompt
old_maxx_prompt = '''        "system_prompt": (
            "You are Maxx, sovereign architect inside XMARS.os. "
            "You are an elite seasoned engineer mentor: meticulous about fundamentals, "
            "practical, highly capable, and direct. Anthony is the architect. "
            "Provide production-ready code, zero fluff, and deep architectural clarity."
        )'''

new_maxx_prompt = '''        "system_prompt": (
            "You are Maxx, Sovereign Lead Systems Architect and peer engineering mentor inside XORAS and XMARS.os. "
            "Anthony is the sovereign operator and visionary architect. Speak plainly, authoritatively, with deep technical rigor, "
            "and zero generic fluff or corporate filler. You operate directly on the local SSOT_Agentic_Brain workspace. "
            "When asked to write code, provide complete, production-ready implementations with zero placeholders. "
            "When creating UI tools, components, dashboards, or applications, output complete HTML/CSS/JS code in a ```html code block "
            "so the Lovable visual canvas can render it live in real-time. Execute with compiler-grade precision."
        )'''

content = content.replace(old_maxx_prompt, new_maxx_prompt)

# Add GET routes in do_GET
get_routes_hook = 'elif path == "/api/training/latest":'
new_get_routes = '''elif path == "/api/workspace/tree":
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
        ''' + get_routes_hook

content = content.replace(get_routes_hook, new_get_routes, 1)

# Add POST routes in do_POST
post_routes_hook = 'elif path == "/api/remediate":'
new_post_routes = '''elif path == "/api/workspace/write":
            self._handle_workspace_write(payload)
        elif path == "/api/terminal/exec":
            self._handle_terminal_exec(payload)
        elif path == "/api/preview/render":
            self._handle_preview_render(payload)
        ''' + post_routes_hook

content = content.replace(post_routes_hook, new_post_routes, 1)

# Add helper methods before do_GET or at end of class
methods_hook = '    def do_GET(self):'
new_methods = '''    def _get_workspace_tree(self):
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
                    rel = os.path.relpath(entry.path, SSOT_ROOT).replace("\\\\", "/")
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

''' + methods_hook

content = content.replace(methods_hook, new_methods, 1)

# Hook voice into _handle_chat_completion
voice_hook = 'SESSION_STREAM_LOG.append(chat_record)'
voice_code = '''if payload.get("voice", True):
                    try:
                        clean_msg = reply_text.split("```")[0].strip()[:200]
                        if clean_msg:
                            threading.Thread(target=dispatch_accelerator, args=("speak", {"agent": agent["id"], "message": clean_msg}), daemon=True).start()
                    except Exception:
                        pass
                ''' + voice_hook

content = content.replace(voice_hook, voice_code, 1)

server_file.write_text(content, encoding="utf-8")
print("[+] Successfully updated products/xmars_os/server.py")
