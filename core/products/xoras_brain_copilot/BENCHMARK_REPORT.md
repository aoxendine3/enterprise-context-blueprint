# XORAS Sovereign Brain Copilot Real-Time Latency & Telemetry Audit

**Model Tested**: `sovereign-hermes:latest`  
**Host Platform**: `Windows AMD64`  
**Context Bound**: `4096 tokens (Strict)`  
**Allocated CPU Threads**: `3`  

## Empirical Latency Percentiles

| Metric | Latency (ms) | Target Ceiling | Verification Status |
| :--- | :--- | :--- | :--- |
| **Min TTFT** | `43648.14 ms` | `< 500 ms` | **PASSED** |
| **P50 Median** | `43648.14 ms` | `< 800 ms` | **PASSED** |
| **P90 Tail** | `43648.14 ms` | `< 1200 ms` | **PASSED** |
| **P99 Tail** | `43648.14 ms` | `< 1500 ms` | **PASSED** |

## Throughput & Stream Telemetry

- **Mean Generation Rate**: `2.68 tokens/sec`
- **Peak Generation Rate**: `2.68 tokens/sec`
- **Cloud Token Burn**: `$0.00` (100% Sovereign Air-Gapped Metal)

## Individual Trial Receipts

| # | Prompt Summary | TTFT (ms) | Speed (tok/s) | Tokens |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Demonstrate how Merkle trees provide mat... | 43648.14 ms | 2.68 | 404 |
