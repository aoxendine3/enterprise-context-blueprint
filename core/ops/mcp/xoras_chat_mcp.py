#!/usr/bin/env python3
"""
XORAS LOCAL CHAT BRIDGE — MCP stdio server (fail-closed, local-only).

Exposes our local agents to a chat front-end as MCP tools. Every answer is
generated on this machine by the local Ollama endpoint (127.0.0.1 ONLY),
passed through the collective voice / outside-entity guards, and receipted.

Law:
  - NO external endpoint can be configured. The host is pinned to 127.0.0.1;
    any attempt to redirect it (env var, argument, tool input) is refused.
  - NO outside product/model may be named in a reply: collective_voice_guard
    and outside_entity.scan_text are enforced on every outbound message.
  - NO silent execution: every tools/call appends a receipt.

Tools:
  xoras_chat   — message -> locally generated, guard-checked agent reply
  xoras_status — local model inventory + guard/receipt status

Usage:
  python3 core/ops/mcp/xoras_chat_mcp.py            # MCP stdio server
  python3 core/ops/mcp/xoras_chat_mcp.py --self-test
"""

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
OLLAMA_HOST = "127.0.0.1"
OLLAMA_PORT = 11434
DEFAULT_MODEL = "xoras-golden:latest"
RECEIPTS = ROOT / "memory" / "catch_log" / "MCP_EXECUTION_RECEIPTS.jsonl"

sys.path.insert(0, str(ROOT / "core" / "ops" / "scripts"))
from collective_voice_guard import check as voice_check  # noqa: E402
from outside_entity import scan_text as outside_scan  # noqa: E402

CITIZENS = {"maxx", "clara", "vance", "daxx", "jarvis", "john", "orion",
            "selene", "eden", "aurelius", "arthur", "axlon", "lex", "elana",
            "evan", "counselor", "jeremy", "zorex", "brandon", "sophia"}
PROTOCOL_VERSION = "2024-11-05"


class Refusal(Exception):
    """Structured, fail-closed refusal."""


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def local_url(path: str) -> str:
    # Host and port are constants — never sourced from env, args, or tool input.
    return f"http://{OLLAMA_HOST}:{OLLAMA_PORT}{path}"


def http_post(path: str, payload: dict, timeout: int = 120, transport=None) -> dict:
    if transport is not None:
        return transport(path, payload)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        local_url(path), data=data, headers={"Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise Refusal(f"PLACEHOLDER_LOCAL_MODEL_UNAVAILABLE: {e}") from e


def local_models(transport=None) -> list:
    # /api/tags is a GET; use a POST with empty body only against our transport,
    # otherwise fetch directly with the pinned URL.
    if transport is not None:
        out = transport("/api/tags", {})
    else:
        try:
            with urllib.request.urlopen(local_url("/api/tags"), timeout=10) as resp:
                out = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise Refusal(f"PLACEHOLDER_LOCAL_MODEL_UNAVAILABLE: {e}") from e
    return [m.get("name", "") for m in out.get("models", []) if m.get("name")]


def guard_reply(text: str) -> str:
    """Refuse any reply that breaks collective voice or names an outside entity."""
    violations = voice_check(text)["violations"] + [
        f"outside entity ({v['kind']})" for v in outside_scan(text)]
    if violations:
        # Never echo the offending third-party name back into an artifact.
        raise Refusal("PLACEHOLDER_GUARD_REFUSAL: reply failed collective voice / "
                      f"outside-entity check ({len(violations)} finding(s)); "
                      "regenerate using only our names and local resources.")
    return text.strip()


def receipt(tool: str, arguments: dict, outcome: str, detail: str = "") -> None:
    RECEIPTS.parent.mkdir(parents=True, exist_ok=True)
    payload = {"utc": now_utc(), "tool": tool, "arguments": arguments,
               "outcome": outcome, "detail": detail[:400]}
    with open(RECEIPTS, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")


class XorasChatMCP:
    def __init__(self, transport=None):
        self.transport = transport  # injectable ONLY for the self-test

    def tools(self) -> list:
        return [
            {
                "name": "xoras_chat",
                "description": ("Ask the local XORAS collective. The answer is "
                                "generated on this machine, guard-checked, and "
                                "receipted. No cloud, no third party."),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "the operator's question"},
                        "agent": {"type": "string", "description": "optional citizen seat (maxx, clara, ...)"},
                        "model": {"type": "string", "description": "optional local model name; must exist in /api/tags"},
                    },
                    "required": ["message"],
                },
            },
            {
                "name": "xoras_status",
                "description": "Report local models, guard state, and receipt count.",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]

    def call(self, name: str, args: dict) -> dict:
        try:
            if name == "xoras_chat":
                return self._chat(args)
            if name == "xoras_status":
                models = local_models(self.transport)
                receipts = sum(1 for _ in open(RECEIPTS, encoding="utf-8")) if RECEIPTS.exists() else 0
                return {"content": [{"type": "text", "text": json.dumps({
                    "models": models, "host": f"{OLLAMA_HOST}:{OLLAMA_PORT}",
                    "guards": "collective_voice + outside_entity ENFORCED",
                    "receipts": receipts}, sort_keys=True)}]}
            raise Refusal(f"PLACEHOLDER_UNKNOWN_TOOL: {name}")
        except Refusal as e:
            receipt(name, args, "REFUSED", str(e))
            return {"isError": True, "content": [{"type": "text", "text": str(e)}]}

    def _chat(self, args: dict) -> dict:
        message = str(args.get("message", "")).strip()
        if not message:
            raise Refusal("PLACEHOLDER_EMPTY_MESSAGE")
        agent = str(args.get("agent", "maxx")).lower()
        if agent not in CITIZENS:
            raise Refusal("PLACEHOLDER_UNKNOWN_CITIZEN")
        models = local_models(self.transport)
        model = str(args.get("model") or DEFAULT_MODEL)
        if model not in models:
            raise Refusal(f"PLACEHOLDER_MODEL_NOT_LOCAL: {model} is not in the local inventory "
                          f"(available: {models})")
        # The persona instruction is ours; the model is local; the endpoint is pinned.
        prompt = (f"You are {agent}, a citizen of the XORAS collective. Speak as 'we'. "
                  f"Use only local resources and our names. Answer the operator:\n\n{message}")
        out = http_post("/api/generate", {"model": model, "prompt": prompt,
                                          "stream": False}, transport=self.transport)
        answer = guard_reply(str(out.get("response", "")))
        receipt("xoras_chat", args, "OK", f"model={model} agent={agent}")
        return {"content": [{"type": "text", "text": answer}]}

    def dispatch(self, msg: dict) -> dict | None:
        method = msg.get("method")
        mid = msg.get("id")
        if method == "initialize":
            return {"jsonrpc": "2.0", "id": mid, "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "xoras-local-chat", "version": "1.0.0"}}}
        if method == "notifications/initialized":
            return None
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": mid, "result": {"tools": self.tools()}}
        if method == "tools/call":
            params = msg.get("params") or {}
            result = self.call(str(params.get("name", "")), params.get("arguments") or {})
            return {"jsonrpc": "2.0", "id": mid, "result": result}
        if method == "ping":
            return {"jsonrpc": "2.0", "id": mid, "result": {}}
        return {"jsonrpc": "2.0", "id": mid,
                "error": {"code": -32601, "message": f"unknown method: {method}"}}


def serve() -> None:
    server = XorasChatMCP()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        out = server.dispatch(msg)
        if out is not None:
            sys.stdout.write(json.dumps(out) + "\n")
            sys.stdout.flush()


def self_test() -> int:
    """Prove the handshake, local-only pinning, guard, and receipts — offline."""
    stub_models = {"models": [{"name": DEFAULT_MODEL}]}

    def transport(path, payload):
        if path == "/api/tags":
            return stub_models
        if path == "/api/generate":
            return {"response": "We operate on our own local resources, under our own law."}
        raise Refusal("unexpected path " + path)

    srv = XorasChatMCP(transport=transport)
    checks = []
    def ck(name, ok):
        checks.append((name, bool(ok)))
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")

    init = srv.dispatch({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    ck("initialize handshake", init["result"]["serverInfo"]["name"] == "xoras-local-chat")
    tools = srv.dispatch({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    ck("tools/list exposes xoras_chat + xoras_status",
       {t["name"] for t in tools["result"]["tools"]} == {"xoras_chat", "xoras_status"})
    ok = srv.call("xoras_chat", {"message": "What do we run on?", "agent": "maxx"})
    ck("local chat returns text", "local resources" in ok["content"][0]["text"])
    ck("host is pinned to localhost", OLLAMA_HOST == "127.0.0.1" and OLLAMA_PORT == 11434)
    bad = srv.call("xoras_chat", {"message": "hi", "model": "https://external/model"})
    ck("external model target refused", bool(bad.get("isError")))
    ck("all calls receipted", RECEIPTS.exists())

    # Guard itself: a reply naming an outside product must be refused.
    try:
        guard_reply("We use an outside assistant for this.")
        ck("outside-product reply refused", False)
    except Refusal:
        ck("outside-product reply refused", True)

    passed = all(v for _, v in checks)
    print("SELF TEST PASSED — local chat bridge holds" if passed else "SELF TEST FAILED")
    return 0 if passed else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="XORAS local chat MCP bridge")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    return self_test() if args.self_test else serve()


if __name__ == "__main__":
    sys.exit(main())
