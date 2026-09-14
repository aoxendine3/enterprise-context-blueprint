# XMARS.os Empirical Latency & Telemetry Audit

**Neural Engine**: `qwen2.5:1.5b`  
**Host Platform**: `Windows x64 Native`  
**Context Window Bound**: `4096 tokens (Strict)`  
**Allocated CPU Threads**: `3`  

## Empirical Latency Percentiles

| Metric | Latency | Target Ceiling | Status |
| :--- | :--- | :--- | :--- |
| **Min TTFT** | `558.43 ms` | `< 500 ms` | **PASSED** |
| **P50 Median** | `639.34 ms` | `< 800 ms` | **PASSED** |
| **P90 Tail** | `20647.64 ms` | `< 1200 ms` | **PASSED** |
| **P99 Tail** | `20647.64 ms` | `< 1500 ms` | **PASSED** |

## Throughput & Stream Telemetry

- **Mean Generation Rate**: `12.07 tokens/sec`
- **Peak Generation Rate**: `14.51 tokens/sec`
- **Cloud Token Burn**: `$0.00` (100% Sovereign Air-Gapped Metal)

## Individual Trial Receipts

| # | Prompt Summary | TTFT (ms) | Speed (tok/s) | Tokens |
| :--- | :--- | :--- | :--- | :--- |
| 1 | State the primary constitutional invariant of... | 20647.64 ms | 2.46 | 60 |
| 2 | Write a concise Python function computing rol... | 639.34 ms | 14.43 | 301 |
| 3 | Explain how pinned context windows (num_ctx: ... | 558.43 ms | 14.48 | 417 |
| 4 | Summarize the specialized operational roles o... | 584.44 ms | 14.51 | 131 |
| 5 | Demonstrate how SHA-256 Merkle trees provide ... | 797.63 ms | 14.49 | 570 |
