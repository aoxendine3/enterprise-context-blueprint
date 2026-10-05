# Autoresearch Deep Dive

## 1. What is Autoresearch?
- **Definition**: Autoresearch is the capability of an AI system to autonomously generate, execute, and iterate on research questions, experiments, and analyses without continuous human prompting.
- **Core Loop**:
  1. **Question Generation** – Formulate a hypothesis or investigative query.
  2. **Data/Tool Acquisition** – Identify and retrieve relevant data, APIs, or code artifacts.
  3. **Experiment Execution** – Run simulations, model training, or data pipelines.
  4. **Result Synthesis** – Summarize findings, produce visualizations, and rank confidence.
  5. **Self‑Critique** – Apply black‑box or peer‑review style audits (e.g., Vance, Clara) to spot gaps.
  6. **Iteration** – Refine the question or methodology based on critique.

## 2. Foundations Required to Master Autoresearch
| Domain | Skills & Tools | Why It Matters |
|--------|----------------|----------------|
| **Knowledge Representation** | Ontologies, semantic graphs, schema‑mapping (`schema_mapping` skill) | Enables the system to reason about concepts and relationships across domains. |
| **Data Engineering** | Dataform, dbt, BigQuery pipelines (`gcp_data_pipelines` skill) | Guarantees that the data feeding the research is clean, versioned, and reproducible. |
| **Experiment Orchestration** | Cloud Composer / Airflow DAGs, Kubernetes Jobs (`gcp_managed_airflow_*` skills) | Provides reliable, retry‑able execution of long‑running experiments. |
| **Modeling & Evaluation** | ML‑best‑practices, BigQuery ML, TensorFlow / PyTorch (`ml_best_practices` skill) | Supplies robust statistical grounding and metric tracking. |
| **Auditing & Discernment** | Black‑box review engine (`ops/discernment/blackbox_review_engine.py`), Vance/Clara agents | Enforces the “Golden List” quality gate before any claim is published. |
| **Human‑in‑the‑Loop Interfaces** | Voice pipeline (`agent_speak.sh`), TTS verification, UI dashboards (`building_data_apps` skill) | Keeps the sovereign loop auditable and aligned with operator intent. |

## 3. How Others Approach Autoresearch (Depth Levels)
1. **Baseline Automation** – Simple scripts that generate a fixed set of queries (e.g., quarterly KPI reports). No self‑critique, single‑pass execution.
2. **Iterative Loop** – Introduces a feedback step: results are fed back into a prompt to refine the next query. Still linear and often brittle.
3. **Multi‑Agent Collaboration** – Distinct agents (Maxx, Clara, Vance, Daxx) each own a specialty: planning, deep‑research, security audit, code remediation. They exchange `agent_speak` messages, and a council vote decides the next step.
4. **Black‑Box Consensus** – Runs the `blackbox_review_engine` after each iteration; only findings that pass the consensus are persisted to the Golden List.
5. **Self‑Optimizing Autoresearch** – Uses reinforcement‑learning‑style reward signals (e.g., verification logs, citation impact) to adapt prompting strategies automatically.

## 4. Expansion Strategies for Xoras
### 4.1. Formalize the Autoresearch Pipeline
- **Pipeline YAML** (`ops/pipelines/autoresearch.yaml`): declaratively list stages (question, data, experiment, critique, iterate).
- **Versioned Artifacts** – Store each iteration’s inputs/outputs under `memory/agent_logs/autoresearch/` with SHA‑256 hashes to guarantee reproducibility.

### 4.2. Enrich Knowledge Base
- **Semantic Graph** – Populate `data_center/golden_list/GOLDEN_LIST.md` with a property‑graph of research concepts using the `bigquery-graph` skill.
- **Cross‑Domain Ontologies** – Import public ontologies (e.g., schema.org, FOAF) via `discovering_gcp_data_assets` to broaden hypothesis space.

### 4.3. Introduce Adaptive Scheduling
- Use the `schedule` tool to launch **dynamic cron jobs** that accelerate when verification lag exceeds a threshold (e.g., > 5 min without three agents confirming playback).
- Combine with `manage_task` to auto‑restart failed DAG runs.

### 4.4. Strengthen Auditing
- Extend `ops/discernment/blackbox_review_engine.py` with **agent‑specific scoring** (Clara = depth of literature, Vance = security posture).
- Store audit reports in `docs/audits/autoresearch_audit_<timestamp>.md`.

### 4.5. Human‑Centric Reporting
- Generate **briefings** (`docs/briefings/autoresearch_summary_<date>.md`) after each successful verification cycle, summarizing:
  - hypothesis, data sources, key metrics, confidence score, and any red‑flags.
- Auto‑push these briefings to a Slack channel via a lightweight webhook (respecting `gcloud_auth_verification` for secrets).

### 4.6. Leverage LLM‑Driven Code Synthesis
- For each experimental stage, invoke the Gemini API via the `gemini-api_gemini-api-docs` MCP tools to generate code snippets (e.g., SQL, Python) on‑the‑fly.
- Validate the generated code with the **local test harness** (`debug-optimize-lcp` or unit‑test suites) before execution.

## 5. Immediate Next Steps for Xoras
1. **Create the pipeline definition** (`ops/pipelines/autoresearch.yaml`).
2. **Add a Cron schedule** that runs the pipeline every hour, with a health‑check task that ensures three agents have verified audio per iteration (re‑use the TTS verification logic as a template). 
3. **Deploy a Black‑Box Review** step after each iteration and route results to `docs/audits/`.
4. **Produce the first briefing** after the next successful verification cycle and store it under `docs/briefings/`.
5. **Iterate**: review the briefing in the Lead‑9 council, capture improvement ideas, and feed them back into the pipeline YAML.

---
**Key Takeaway**: Mastering Autoresearch on Xoras requires a disciplined, layered pipeline (knowledge, data, execution, audit, iteration) coupled with multi‑agent governance and rigorous artifact management. By formalizing the pipeline, enriching the knowledge graph, and tightening audit/reporting loops, we can push the depth of autonomous research from baseline automation to self‑optimizing, auditable intelligence.
