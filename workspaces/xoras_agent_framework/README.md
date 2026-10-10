# XORAS Agentic Environment & Governance Framework v2.0

![XORAS Hero Banner](docs/assets/xoras_hero_banner.jpg)

[![PyPI Version](https://img.shields.io/pypi/v/xoras-agent-framework.svg?color=blue)](https://pypi.org/project/xoras-agent-framework/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![AST Security](https://img.shields.io/badge/AST%20Security-100%25%20PASSED-brightgreen.svg)](#ast-static-security-gating)
[![Build](https://img.shields.io/badge/tests-9%20passed-brightgreen.svg)](#testing)

**XORAS Agentic Environment & Governance Framework** is an enterprise-grade multi-agent runtime, dynamic AST security scanner, and cryptographic provenance platform developed by **XORAS Systems LLC**.

---

## 🛡️ AST Security Architecture & Guardrails

![XORAS AST Security Shield Architecture](docs/assets/xoras_ast_security_shield.jpg)

## Key Features

- **AST Static Security Gating (`env-integrity-sentry`)**: Real-time Abstract Syntax Tree parsing and secret scanning that intercepts dangerous code injections (`eval`, `exec`, `subprocess shell=True`) and credential leaks prior to execution.
- **Cryptographic Trace Receipts (`xoras.evidence.v1`)**: Every agent state transition and tool invocation generates an Ed25519 / HMAC SHA-256 signed JSON-L trace receipt for 100% zero-falsification audit trails.
- **Enterprise SIEM & Log Exporters**: Formatted log streaming plugins for **Datadog**, **Splunk**, **Elasticsearch**, and **Syslog**.
- **Automated SOC2 & ISO 27001 AI Compliance Auditor**: Built-in compliance auditor (`SOC2ComplianceAuditor`) that evaluates trace receipts and issues automated audit certificates.
- **Polyglot & WASM Micro-Runtime IPC Bridge**: Extends security gating to external C++, Rust, Zig, and WASM binary micro-runtimes.
- **Pre-Commit Git Integration**: Standalone `.pre-commit-hooks.yaml` config allowing engineering teams to run `xoras scan` in git pre-commit hooks.

---

## Architecture Overview

```mermaid
flowchart TD
    UserRequest["User / Trigger Payload"] --> SwarmOrchestrator["Swarm Orchestrator (Architect)"]
    SwarmOrchestrator --> ASTEngine["AST Security Engine (Auditor)"]
    
    ASTEngine -- "Pass (Safety Score = 1.0)" --> RuntimeHarness["XORAS Runtime Harness (Engineer)"]
    ASTEngine -- "Fail (Restricted Token)" --> RejectReceipt["Log Rejection & Signed Receipt"]
    
    RuntimeHarness --> ToolExec["Subprocess / File I/O Sandbox"]
    ToolExec --> EvidenceSigner["Cryptographic Signer (HMAC / Ed25519)"]
    EvidenceSigner --> JSONLTrace["xoras_agent_traces.jsonl"]
```

---

## Quickstart & Installation

### 1. Install Package
```bash
pip install xoras-agent-framework
```

### 2. Initialize Governance Environment
```bash
xoras init
```
This generates `.xorasrules` and `xoras.env.yaml` in your workspace root.

### 3. Scan Scripts for AST Violations
```bash
xoras scan my_script.py
```

### 4. Run Scripts in Isolated Sandbox
```bash
xoras run my_script.py
```

### 5. Serve Interactive Web Dashboard
```bash
xoras serve --port 8080
```
Open `http://localhost:8080` to view the live product landing page and interactive AST playground.

---

## Python API Usage

```python
from xoras import XORASAgentEnvironment, SwarmOrchestrator

# Initialize environment
env = XORASAgentEnvironment(config_path="xoras.env.yaml")

# Run multi-agent orchestrator pipeline
orchestrator = SwarmOrchestrator(env=env)
result = orchestrator.run_pipeline(
    task_description="Deploy verified configuration file",
    code_payload='{"status": "active", "version": "2.0.0"}',
    target_path="artifacts/deploy_config.json"
)

print("Pipeline Success:", result["success"])
print("Trace Signature:", result["last_signature"])
```

---

## Testing

Run the automated test suite:
```bash
PYTHONPATH=. pytest tests/
```

---

## Documentation

- [AST Security Gating Specification](docs/architecture/AST_SECURITY_GATING.md)
- [Cryptographic Provenance Receipts](docs/architecture/CRYPTOGRAPHIC_PROVENANCE.md)
- [API Reference](docs/API_REFERENCE.md)

---

## License

Distributed under the MIT Enterprise License. See `LICENSE` for details.  
&copy; 2026 XORAS Systems LLC. All rights reserved.
