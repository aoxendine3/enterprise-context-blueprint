"""
XORAS Systems LLC — CLI Tooling Entrypoint (xoras-cli)
Command line interface for initializing environments, running AST security scans, and serving web dashboards.
"""

import argparse
import json
import os
import sys
import http.server
import socketserver
import webbrowser
from typing import List

from .config import XORASConfig
from .ast_security import ASTSecurityEngine
from .runtime import XORASAgentEnvironment
from .orchestrator import SwarmOrchestrator

DEFAULT_RULES = """# XORAS SYSTEMS LLC — AGENTIC ENVIRONMENT & GOVERNANCE SPECIFICATION

[AGENT_IDENTITY]
Entity: XORAS Autonomous Agent Node
Architecture: Multi-Agent Orchestrator (XORAS Swarm)
Governance Policy: Strict Execution Guardrails & AST Safety Verification

[OPERATIONAL_DIRECTIVES]
1. AUTONOMOUS_EXECUTION: Resolve intent via iterative state evaluation, tool invocation, and self-correction prior to human escalation.
2. AST_SECURITY_GATING: All dynamic code execution, subprocess calls, and external payloads must pass AST static analysis and secret scanning (`env-integrity-sentry`).
3. ZERO_DRIFT_BRANDING: Enforce XORAS Systems LLC branding across all client-facing artifacts, logs, and generated assets. Legacy naming is prohibited.
4. DETERMINISTIC_LOGGING: Every agent state transition, tool call, and FFI interaction must produce structured JSON-L traces.
"""

DEFAULT_ENV_YAML = """version: "2.0.0"
organization: "XORAS Systems LLC"
runtime:
  environment_type: "agentic-sandbox"
  concurrency_limit: 8
  default_timeout_seconds: 120
  memory_limit_mb: 4096

security:
  ast_verification: true
  allow_network_egress: true
  allowed_domains:
    - "github.com"
    - "pypi.org"
  secret_scanner: "env-integrity-sentry"
  block_deprecated_branding: true

agent_swarm:
  orchestrator:
    model: "gemini-2.5-flash"
    temperature: 0.1
    max_tokens: 8192
  agents:
    - name: "Architect"
      role: "System design, specification authoring, and state graph planning"
      capabilities: ["file_read", "file_write", "diagram_gen"]
    - name: "Engineer"
      role: "Code generation, refactoring, and AST verification"
      capabilities: ["file_read", "file_write", "bash_exec", "test_runner"]
    - name: "Auditor"
      role: "Security scanning, secret detection, and runtime compliance"
      capabilities: ["ast_scan", "log_audit", "policy_check"]

paths:
  workspace_root: "."
  log_output: "./logs/xoras_agent_traces.jsonl"
  artifact_store: "./artifacts"
"""

def init_cmd():
    print("[XORAS CLI] Initializing XORAS Agentic Governance Environment...")
    if not os.path.exists(".xorasrules"):
        with open(".xorasrules", "w", encoding="utf-8") as f:
            f.write(DEFAULT_RULES)
        print(" -> Created .xorasrules")
    else:
        print(" -> .xorasrules already exists.")

    if not os.path.exists("xoras.env.yaml"):
        with open("xoras.env.yaml", "w", encoding="utf-8") as f:
            f.write(DEFAULT_ENV_YAML)
        print(" -> Created xoras.env.yaml")
    else:
        print(" -> xoras.env.yaml already exists.")
        
    os.makedirs("logs", exist_ok=True)
    os.makedirs("artifacts", exist_ok=True)
    print("[XORAS CLI] Initialization complete. Your workspace is secured with XORAS AST Guardrails.")

def scan_cmd(target_file: str):
    print(f"[XORAS CLI] Running AST Security Scan on target: '{target_file}'")
    if not os.path.exists(target_file):
        print(f"Error: Target file or directory '{target_file}' not found.")
        sys.exit(1)
        
    files_to_scan: List[str] = []
    if os.path.isdir(target_file):
        for root, _, files in os.walk(target_file):
            for file in files:
                if file.endswith(".py"):
                    files_to_scan.append(os.path.join(root, file))
    else:
        files_to_scan.append(target_file)

    engine = ASTSecurityEngine()
    total_violations = 0
    total_secrets = 0
    any_failed = False

    for file_path in files_to_scan:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        result = engine.scan_code(code)
        print(f"\n--- AST SCAN REPORT: {file_path} ---")
        print(f"Status: {'PASSED [SAFE]' if result.is_safe else 'REJECTED [UNSAFE]'}")
        print(f"Safety Score: {result.safety_score * 100:.1f}% | AST Nodes Analyzed: {result.nodes_analyzed}")

        if result.violations:
            total_violations += len(result.violations)
            print("Violations Detected:")
            for v in result.violations:
                print(f" - {v}")

        if result.secrets_detected:
            total_secrets += len(result.secrets_detected)
            print("Secret Leaks Detected:")
            for s in result.secrets_detected:
                print(f" - {s}")

        if not result.is_safe:
            any_failed = True

    print(f"\n[XORAS CLI Summary] Scanned {len(files_to_scan)} file(s). Total Violations: {total_violations} | Total Secret Warnings: {total_secrets}")
    if any_failed:
        sys.exit(2)

def run_cmd(target_file: str):
    print(f"[XORAS CLI] Executing script '{target_file}' under XORAS Sandboxed Runtime...")
    if not os.path.exists(target_file):
        print(f"Error: Target file '{target_file}' not found.")
        sys.exit(1)
        
    with open(target_file, "r", encoding="utf-8") as f:
        code = f.read()

    env = XORASAgentEnvironment()
    res = env.execute_tool("Engineer", "bash_exec", {"command": f"{sys.executable} {target_file}"})
    
    print("\n--- EXECUTION OUTPUT ---")
    print(res.get("stdout", ""))
    if res.get("stderr"):
        print("STDERR:", res.get("stderr"))
    print(f"Exit Code: {res.get('exit_code', -1)}")
    print(f"Trace Receipt Signature: {res.get('receipt_signature', 'NONE')}")

def serve_cmd(port: int = 8080):
    web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web")
    if not os.path.exists(web_dir):
        web_dir = os.path.join(os.getcwd(), "web")

    if not os.path.exists(web_dir):
        print(f"Error: Web dashboard directory '{web_dir}' not found.")
        sys.exit(1)

    os.chdir(web_dir)
    Handler = http.server.SimpleHTTPRequestHandler
    print(f"[XORAS CLI] Serving Web Product Page & Live Dashboard at http://localhost:{port}")
    try:
        with socketserver.TCPServer(("", port), Handler) as httpd:
            print(f"[XORAS CLI] Server running. Press Ctrl+C to stop.")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[XORAS CLI] Server stopped.")

def main():
    parser = argparse.ArgumentParser(description="XORAS Systems LLC — Agentic Framework CLI")
    subparsers = parser.add_subparsers(dest="command")

    # init command
    init_p = subparsers.add_parser("init", help="Initialize .xorasrules and xoras.env.yaml in current workspace")

    # scan command
    scan_p = subparsers.add_parser("scan", help="Run AST security and secret scan on a script")
    scan_p.add_argument("file", help="Python or shell script to scan")

    # run command
    run_p = subparsers.add_parser("run", help="Run a script through XORAS agentic runtime")
    run_p.add_argument("file", help="Python script to run")

    # serve command
    serve_p = subparsers.add_parser("serve", help="Serve interactive product landing page and dashboard")
    serve_p.add_argument("--port", type=int, default=8080, help="Port to serve on (default: 8080)")

    args = parser.parse_args()
    if args.command == "init":
        init_cmd()
    elif args.command == "scan":
        scan_cmd(args.file)
    elif args.command == "run":
        run_cmd(args.file)
    elif args.command == "serve":
        serve_cmd(args.port)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
