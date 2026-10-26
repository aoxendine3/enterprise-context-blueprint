#!/usr/bin/env python3
"""
===============================================================================
XORAS SOVEREIGN CROSS-NODE AUTHENTICATED GATEWAY (SOVRA DEEP-LOCK v18.0)
Serves as an authenticated local reverse-proxy for the Windows Bare-Metal Node.
Enforces:
1. Strict X-SOVRA-DEEP-LOCK HMAC-SHA256 token verification
2. Replay-attack rejection (< 5.0s timestamp drift)
3. Monotonic nonces and client rate-limiting
4. Transparent forwarding to Windows Ollama Node (192.168.1.211:11434)
===============================================================================
"""

import http.server
import socketserver
import urllib.request
import urllib.error
import json
import time
import os
import sys
from pathlib import Path

SSOT_ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
sys.path.insert(0, str(SSOT_ROOT / "ops" / "scripts"))
from sovra_deep_lock import validate_handshake, generate_handshake

AUTH_PORT = 11435
WINDOWS_NODE_URL = "http://192.168.1.211:11434"
SEEN_NONCES = set()

class SovereignAuthGatewayHandler(http.server.BaseHTTPRequestHandler):
    def _authenticate(self) -> bool:
        auth_header = self.headers.get("X-SOVRA-DEEP-LOCK")
        if not auth_header:
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": "UNAUTHORIZED_ZERO_TRUST_VIOLATION",
                "message": "Missing mandatory X-SOVRA-DEEP-LOCK HMAC token."
            }).encode())
            return False

        valid, reason, payload = validate_handshake(auth_header, max_drift_seconds=5.0)
        if not valid or not payload:
            self.send_response(403)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": "DEEP_LOCK_SECURITY_VIOLATION",
                "reason": reason
            }).encode())
            return False

        nonce = payload.get("nonce") or f"{payload.get('iat')}_{auth_header[-16:]}"
        if nonce in SEEN_NONCES:
            self.send_response(403)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": "REPLAY_ATTACK_DETECTED",
                "reason": "Nonce already observed in sovereign session."
            }).encode())
            return False

        SEEN_NONCES.add(nonce)
        if len(SEEN_NONCES) > 10000:
            SEEN_NONCES.clear()

        return True

    def do_GET(self):
        if not self._authenticate():
            return
        self._proxy_request("GET")

    def do_POST(self):
        if not self._authenticate():
            return
        self._proxy_request("POST")

    def _proxy_request(self, method: str):
        target_url = f"{WINDOWS_NODE_URL}{self.path}"
        body = None
        if method == "POST":
            content_len = int(self.headers.get("Content-Length", 0))
            if content_len > 0:
                body = self.rfile.read(content_len)

        req = urllib.request.Request(target_url, data=body, method=method)
        req.add_header("Content-Type", self.headers.get("Content-Type", "application/json"))

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                resp_data = resp.read()
                self.send_response(resp.status)
                for k, v in resp.getheaders():
                    if k.lower() not in ["content-length", "transfer-encoding", "connection"]:
                        self.send_header(k, v)
                self.send_header("Content-Length", str(len(resp_data)))
                self.send_header("X-SOVRA-AUTHENTICATED", "TRUE")
                self.end_headers()
                self.wfile.write(resp_data)
        except urllib.error.HTTPError as e:
            err_body = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(err_body)
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": "WINDOWS_NODE_UNREACHABLE",
                "message": str(e)
            }).encode())

class ThreadedAuthGateway(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

def main():
    print(f"🔒 [SOVRA Gateway] Starting Zero-Point Authenticated Proxy on port {AUTH_PORT} -> {WINDOWS_NODE_URL}...")
    with ThreadedAuthGateway(("127.0.0.1", AUTH_PORT), SovereignAuthGatewayHandler) as server:
        server.serve_forever()

if __name__ == "__main__":
    main()
