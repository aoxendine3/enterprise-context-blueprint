# Research Proposal Template (Structured by FINER & PICOT)

> **Purpose:** Provide a repeatable, governance‑compliant scaffold for turning any identified research gap into a fully‑specified study design.  
> **Audience:** Researchers, data‑engineers, compliance officers, and the Lead 9 Council.

## 1. Title & Gap Identification
- **Working Title:** *[Insert concise title]*
- **Gap Type:** *(Select one from the taxonomy – see `research_gap_taxonomy.md`)*  
- **Gap Statement (≈ 2 sentences):** *[Describe the specific deficiency in the literature or practice]*

## 2. FINER Criteria (Feasibility, Interest, Novelty, Ethics, Relevance)
| Criterion | Assessment (Yes/No) | Rationale |
|-----------|--------------------|-----------|
| **Feasibility** | | *Availability of data, resources, timeline* |
| **Interest**    | | *Stakeholder demand, strategic importance* |
| **Novelty**     | | *Is this gap unaddressed?* |
| **Ethics**      | | *Compliance with regulatory and ethical standards* |
| **Relevance**   | | *Alignment with business or scientific objectives* |

## 3. PICOT Elements (Population, Intervention, Comparison, Outcome, Timing)
| Element | Definition |
|---------|------------|
| **Population** | *Specify sub‑group (e.g., “US‑based fintech customers ≥ 30 y/o”)* |
| **Intervention** | *What will be introduced, measured, or changed?* |
| **Comparison** | *Control condition or baseline (if any)* |
| **Outcome** | *Primary & secondary metrics (e.g., hallucination rate, compliance score)* |
| **Timing** | *Study duration, measurement intervals* |

## 4. Methodology (aligned to Gap Type)
- **Design:** *[e.g., Randomised Controlled Trial, Observational Cohort, Mixed‑Methods]*
- **Data Sources:** *[e.g., `.sovereign/world_file.db`, GraphRAG knowledge graph, external APIs]*
- **Instrumentation:** *[e.g., `gemini‑search‑docs`, `sovra_process_intake_signal`, custom Python analytics]*
- **Statistical Plan:** *[Power analysis, regression models, Bayesian updates]*

## 5. Risk & Mitigation (Trinity‑Gate Alignment)
| Risk | Impact | Mitigation |
|------|--------|------------|
| **High‑risk hallucination** (if gap = Empirical) | Potential regulatory breach | Deploy dual‑model verification, enforce HITL for all high‑risk outputs |
| **Data‑privacy breach** | Legal exposure | Apply ch‑flags immutable, enforce `gcloud` IAM least‑privilege |
| **Methodological bias** | Invalid conclusions | Use cross‑validation with at least two independent methods (Methodological Gap) |

## 6. Deliverables & Timeline
- **Milestone 1:** Gap validation & data‑catalogue (2 weeks)
- **Milestone 2:** Prototype experiment (4 weeks)
- **Milestone 3:** Full‑scale study & audit receipt (6 weeks)
- **Final Artefact:** `docs/audits/<PROJECT>_GAUNTLET_RECEIPT.json` (signed, Merkle‑rooted)

## 7. Governance Sign‑Off (Trinity Gate)
- **Agents:** Maxx, Clara, Vance – each emits audio heartbeat, computes SHA‑256 hash, and logs to `memory/agent_logs/`.  
- **Pass Condition:** 2‑out‑of‑3 distinct hashes → **PASS** → proposal becomes active.
