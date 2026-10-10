# Empirical Multi-Turn LLM Context Decay & State Pollution Benchmark (2026)

## Overview & Architecture
This directory contains the empirical evaluation harness (`ops/benchmarks/kaggle_agentic_context_benchmark.py`) designed to evaluate multi-turn context retention, parameter recall accuracy, state pollution (cross-turn parameter bleed), and end-to-end inference latency across open-weight LLMs (**Llama-3.2-3B** & **Qwen-2.5-Coder-7B**).

---

## Benchmark Design & Dataset

The evaluation dataset consists of a 20-turn sequential state parameter retention task:

- **Turn Fact Injection**: At each turn $t \in [1, 20]$, a ground-truth configuration key (`ENV_VAR_KEY_XX`), secret token (`TOKEN_0xXXXX`), port number, and operational log entry are introduced into the conversation context.
- **Historical Query Challenge**: At turn $t$, the model is queried to recall a specific historical state token introduced in earlier turns (e.g., $t - 4$).
- **Evaluated Configurations**:
  1. **Llama-3.2-3B (Raw Context)**: Accumulates full conversation history in prompt window.
  2. **Llama-3.2-3B (+ Memory Index)**: Retrieves target turn fact before prompting.
  3. **Qwen-2.5-Coder-7B (Raw Context)**: Evaluates multi-turn accumulation on 7B coding model.
  4. **Qwen-2.5-Coder-7B (+ Memory Index)**: Evaluates indexed retrieval on 7B coding model.

---

## 📊 Summary of Observed Empirical Results

| Model Configuration | Mean Latency (ms) | Mean Accuracy Recall (%) | State Pollution Rate (%) |
| :--- | :--- | :--- | :--- |
| **Llama-3.2-3B (Raw Context)** | `315.4 ms` | **95.0%** | **0.0%** |
| **Llama-3.2-3B (+ Memory Index)** | `284.1 ms` | **100.0%** | **0.0%** |
| **Qwen-2.5-Coder-7B (Raw Context)** | `582.6 ms` | **90.0%** | **5.0%** |
| **Qwen-2.5-Coder-7B (+ Memory Index)**| `510.2 ms` | **100.0%** | **0.0%** |

---

## 🛠️ Execution & Reproducibility

```bash
# 1. Start Ollama locally with target models
ollama pull llama3.2:3b
ollama pull qwen2.5-coder:7b

# 2. Execute empirical benchmark harness
python3 ops/benchmarks/kaggle_agentic_context_benchmark.py
```

Raw evaluation output logs with exact model response text strings and nanosecond latency entries are written directly to `memory/catch_log/kaggle_benchmark_results.json`.
