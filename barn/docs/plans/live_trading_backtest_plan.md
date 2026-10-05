# Live‑Trading Back‑Test Milestone – Project Plan

## Objective
Demonstrate **real‑world, profitable, autonomous trading** using the full XORAS swarm + FPGA BNN stack. This satisfies AGI proof points #1 (human‑level performance), #3 (autonomy & self‑improvement), and #5 (embodied interaction) by running a live back‑test over **6 months of market data**.

## Scope
- **Assets**: US equities, crypto, commodities – any market with high‑frequency data.
- **Timeframe**: Historical 6‑month window (e.g., 2025‑06‑01 → 2025‑12‑01) for back‑test, then a **30‑day live paper‑trading** pilot.
- **Components**: 
  1. **Data ingest** – `xoras_live_ingestion.py` pulls tick‑level data into the shared memory fabric.
  2. **Feature engine** – `xoras_vector_db.py` creates embeddings, feeds the 1‑bit BNN (`xoras_hyper_fracture.py`).
  3. **Decision swarm** – `xoras_swarm_manager.py` coordinates 22 agents, each with private journal snapshots.
  4. **Execution layer** – `xoras_omni_core.py` interfaces with a broker API (demo Alpaca sandbox).
  5. **Self‑healing** – `fortify_memory_schizophrenia.py` monitors memory integrity; `xoras_hyper_fracture.py` detects and repairs fracturing.

## Deliverables
| ID | Artifact | Description | Owner |
|----|----------|-------------|-------|
| **D1** | **Back‑test notebook** (`backtest.ipynb`) | Runs the full pipeline on historical data, computes Sharpe, max‑drawdown, win‑rate. | Clara (research) |
| **D2** | **Live‑paper‑trading script** (`paper_trading.py`) | Deploys the swarm to Alpaca sandbox, logs PnL each minute. | Vance (security) |
| **D3** | **Verification report** (`docs/audits/live_trading_report.md`) | Independent audit of logs, reproducibility checklist, statistical significance test. | Jarvis (governance) |
| **D4** | **Docker image** (`xoras/trading‑engine:latest`) | Encapsulates the entire stack, version‑pinned, signed with macOS code‑signing. | Maxx (coordination) |

## Milestones & Timeline (30 days total)
| Milestone | Target Date | Success Criteria |
|-----------|------------|------------------|
| **M1 – Data pipeline ready** | Day 3 | Ingest 1 M rows without errors, stored in `memory_fabric`. |
| **M2 – BNN inference validated** | Day 5 | BNN outputs deterministic predictions (unit‑test with fixed seed). |
| **M3 – Swarm decision loop** | Day 8 | All 22 agents produce a consensus trade signal within 200 ms. |
| **M4 – Back‑test completed** | Day 12 | Sharpe > 1.5, max‑drawdown < 10 %, statistically significant (p < 0.01). |
| **M5 – Security audit** | Day 15 | No data leakage, memory‑sanity checks pass, Docker image signed. |
| **M6 – Live paper‑trading** | Day 20‑30 | Daily PnL > 0 % on average, autonomy: no human‑intervention logs. |
| **M7 – Final audit & report** | Day 31 | Jarvis signs off the `live_trading_report.md`. |

## Verification & Proof Strategy
1. **Deterministic builds** – All binaries (C++ libmodel, FPGA HLS, Docker image) built with exact version pins; SHA‑256 hashes stored in `docs/plans/build_hashes.md`.
2. **Statistical validation** – Run a paired‑t test against a baseline strategy (e.g., market‑cap weighted index) to prove out‑performance.
3. **Independent replication** – Publish the Docker image and a `seed.txt` file; any external party can rerun the back‑test and obtain identical metrics.
4. **Audit trail** – Each agent writes to its private journal (`memory/journals/agents/`); the consolidated log is hashed and posted to a public gist for transparency.
5. **Safety checks** – Vance’s security scan runs pre‑flight and post‑flight; any breach aborts the run and triggers the kill‑switch (`xoras_kill_switch.py`).

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Data feed latency | Missed signal windows | Buffer incoming ticks, fallback to last‑known price. |
| Model drift after back‑test | Future degradation | Enable `fortify_memory_schizophrenia` to trigger auto‑re‑training on new data. |
| Regulatory compliance | Legal exposure | Use only sandbox broker APIs; keep audit logs immutable. |
| hardware failure (FPGA) | System halt | Have software fallback (`xoras_swarm_manager` runs in pure CPU mode). |

## Acceptance Criteria
- **Profitability**: Net PnL ≥ +5 % over the 30‑day paper‑trading window.
- **Reproducibility**: Running the same Docker image with the same `seed.txt` yields identical back‑test metrics (within 0.01 %).\n- **Audit sign‑off**: Jarvis stamps the `live_trading_report.md` as *Golden List compliant*.
- **Safety**: No unauthorized outbound network connections; all logs are write‑once.

---
*Prepared by Maxx (Xoras/Maxx) – coordinating the swarming agents to close the AGI proof loop.*
