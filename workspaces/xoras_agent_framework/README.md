# XORAS Agentic Environment & Governance Framework v2.4.0

![XORAS Hero Banner](docs/assets/xoras_hero_banner.jpg)

[![PyPI Version](https://img.shields.io/pypi/v/xoras-agent-framework.svg?color=blue)](https://pypi.org/project/xoras-agent-framework/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![MTPO Concurrency](https://img.shields.io/badge/MTPO-17.39M%20ops%2Fsec-blue.svg)](https://aoxendine3.github.io/mtpo/)
[![Hot-Spot p99](https://img.shields.io/badge/hot--spot%20p99-2.0%20%C2%B5s-emerald.svg)](https://raw.githubusercontent.com/aoxendine3/mtpo/main/VERIFICATION_RECEIPT.md)
[![AST Security](https://img.shields.io/badge/AST%20Security-100%25%20PASSED-brightgreen.svg)](#ast-static-security-gating)
[![Build](https://img.shields.io/badge/tests-passing-brightgreen.svg)](#testing)

**XORAS Agentic Environment & Governance Framework** is an enterprise-grade multi-agent runtime, dynamic AST security scanner, lock-free concurrency engine (**MTPO**), and cryptographic provenance platform developed by **XORAS Systems LLC**.

---

## 🌐 Live Verified Proving Grounds

* **🛡️ UPGP v5.0 Proving Ground**: [https://aoxendine3.github.io/upgp-proving-ground/](https://aoxendine3.github.io/upgp-proving-ground/)
* **⚡ MTPO Concurrency Engine**: [https://aoxendine3.github.io/mtpo/](https://aoxendine3.github.io/mtpo/)
* **🪐 MARS Reasoning Structure**: [https://aoxendine3.github.io/mars/](https://aoxendine3.github.io/mars/)
* **📐 REASONS Semantic Canvas**: [https://aoxendine3.github.io/reasons/](https://aoxendine3.github.io/reasons/)
* **📜 Raw Physical Silicon Receipt**: [https://raw.githubusercontent.com/aoxendine3/mtpo/main/VERIFICATION_RECEIPT.md](https://raw.githubusercontent.com/aoxendine3/mtpo/main/VERIFICATION_RECEIPT.md)

---

## Key Features

- **⚡ MTPO Lock-Free Concurrency Engine**: Monotonic Trajectory Pre-Order synchronization (`HexCellRing`) with 128-byte cache-line alignment, sustaining **17.39M ops/sec** with **2.0 µs hot-spot p99 latency** and zero thread deadlocks.
- **🔄 Deterministic 3-Phase Saga Undo**: Reverse speculative agent failures via algebraic inverse rollbacks ($\Delta_B^{-1} \circ \Delta_B \equiv \text{id}$ proved confluent in Z3 `AUFBV`). 128-step swarm rollbacks complete in **0.875 µs on-core CPU time**.
- **📜 Context Lineage Merkle DAG Engine**: Cryptographically anchors every agent deliberation and state transition into content-addressed DAG nodes with dynamic tip-root calculation and zero-state-pollution quarantine (`ContextLineageDAGEngine`).
- **🛡️ AST Static Security Gating (`env-integrity-sentry`)**: Real-time Abstract Syntax Tree parsing and secret scanning that intercepts dangerous code injections (`eval`, `exec`, `subprocess shell=True`) and credential leaks prior to execution.
- **🔏 Cryptographic Trace Receipts (`xoras.evidence.v1`)**: Every agent state transition and tool invocation generates an Ed25519 / HMAC SHA-256 signed JSON-L trace receipt for 100% zero-falsification audit trails.
- **📊 Enterprise SIEM & Log Exporters**: Formatted log streaming plugins for **Datadog**, **Splunk**, **Elasticsearch**, and **Syslog**.
- **⚖️ Automated SOC2 & ISO 27001 AI Compliance Auditor**: Built-in compliance auditor (`SOC2ComplianceAuditor`) that evaluates trace receipts and issues automated audit certificates.

---

## Installation & Quickstart

```bash
pip install xoras-agent-framework
```

### 1. Multi-Agent Concurrency with MTPO HexCell Ring

```python
from xoras import HexCellRing

# Initialize 128-byte cache-aligned lock-free ring
ring = HexCellRing()

# Commit speculative state on Slot 0
committed = ring.execute_saga(slot_idx=0, tx_id=101, new_val=0xBEAF0001)
print("Committed:", committed, "Value:", hex(ring.read(0)))

# Automatic Saga rollback on constraint failure
rolled_back = not ring.execute_saga(slot_idx=0, tx_id=102, new_val=0xDEADBEEF, inject_fault=True)
print("Rolled Back:", rolled_back, "State Preserved:", hex(ring.read(0)))
```

### 2. Immutable Context Lineage Merkle DAG

```python
from xoras import ContextLineageDAGEngine

dag = ContextLineageDAGEngine()

# Commit genesis and child nodes
ok, hash1, _ = dag.commit("genesis", [], {"model": "claude-3-5-sonnet", "action": "PLAN"})
ok, hash2, _ = dag.commit("step_1", ["genesis"], {"action": "RESEARCH", "data": "retrieved"})

print("Dynamic Merkle Root:", dag.get_dynamic_merkle_root())

# Anti-replay invariant rejects duplicate payloads across unlinked sessions
ok, _, err = dag.commit("replay_attack", [], {"action": "RESEARCH", "data": "retrieved"})
print("Replay Intercepted & Quarantined:", not ok, "Error:", err)
```

### 3. AST Security Scanning CLI

```bash
xoras scan my_agent_script.py
xoras run my_agent_script.py
```

---

## Physical Hardware Verification (Apple Silicon M4)

All concurrency rates and rollback latencies are verified on physical hardware:
- **POSIX Shared Memory**: 9.20 MB buffer mapped via `shm_open` + `mmap` with `MAP_SHARED`.
- **Throughput**: 7.98M ops/sec sustained under concurrent multi-agent writes.
- **Full Swarm Rollback**: 128 speculative steps reverted in **0.875 µs on-core CPU time**.
- **Formal Confluence**: Z3 returns `unsat` in 0.002s for Saga inverse reduction.

See [`VERIFICATION_RECEIPT.md`](https://raw.githubusercontent.com/aoxendine3/mtpo/main/VERIFICATION_RECEIPT.md) for full physical receipts.

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
