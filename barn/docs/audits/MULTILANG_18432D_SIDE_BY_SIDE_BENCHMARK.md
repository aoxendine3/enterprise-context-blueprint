# 🏆 XORAS 5-LANGUAGE SIDE-BY-SIDE BARE-METAL BENCHMARK REPORT

> **Workload**: 100,000 18,432-D Hexological Vector Nodes (7.37 GB Vector Data)
> **Substrate**: Apple Silicon M4 Bare Metal (`aarch64-apple-darwin`, 10 CPU Cores)
> **Timestamp**: 2026-09-29 10:46:52 UTC

| Language Runtime | Execution Time | Vector Throughput | GFLOPS (ARM64) | Memory Bandwidth | p50 Latency | p99 Latency |
|---|---|---|---|---|---|---|
| **M4 LPDDR5X Hardware STREAM Baseline** | `21.03 ms` | `0 evals/sec` | `0.00 GFLOPS` | `95.10 GB/s` | `0.00 µs` | `0.00 µs` |
| **SOVRA C/NEON (clang -O3)** | `70.68 ms` | `1,414,845 evals/sec` | `52.16 GFLOPS` | `97.15 GB/s` | `0.70 µs` | `0.93 µs` |
| **C++20 (clang++ -O3)** | `71.60 ms` | `1,396,690 evals/sec` | `51.49 GFLOPS` | `95.90 GB/s` | `0.72 µs` | `0.77 µs` |
| **Rust 1.95 (Cargo + Rayon)** | `69.49 ms` | `1,438,979 evals/sec` | `53.05 GFLOPS` | `98.81 GB/s` | `0.69 µs` | `0.72 µs` |
| **Zig 0.16 (ReleaseFast)** | `69.80 ms` | `1,432,658 evals/sec` | `52.81 GFLOPS` | `98.37 GB/s` | `0.70 µs` | `0.73 µs` |
| **Go 1.22 (go build)** | `97.40 ms` | `1,026,693 evals/sec` | `37.85 GFLOPS` | `70.50 GB/s` | `0.94 µs` | `1.34 µs` |
