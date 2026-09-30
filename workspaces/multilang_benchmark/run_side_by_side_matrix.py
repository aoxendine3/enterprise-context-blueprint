#!/usr/bin/env python3
"""
XORAS 5-LANGUAGE SIDE-BY-SIDE BARE-METAL BENCHMARK MATRIX
Workload: 100,000 18,432-D Hexological Vector Nodes (7.37 GB Vector Data)
Runtimes: C++20, Rust 1.95, Zig, Go 1.22, SOVRA C/NEON
Substrate: Apple Silicon M4 Bare Metal (10 CPU Cores)
"""

import os
import sys
import json
import subprocess
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "../.."))

CPP_DIR = os.path.join(BASE_DIR, "cpp")
GO_DIR = os.path.join(BASE_DIR, "go")
ZIG_DIR = os.path.join(BASE_DIR, "zig")
SOVRA_DIR = os.path.join(BASE_DIR, "sovra_c")
RUST_DIR = os.path.join(ROOT_DIR, "workspaces/hexological_engine")

REPORT_MD = os.path.join(ROOT_DIR, "docs/audits/MULTILANG_18432D_SIDE_BY_SIDE_BENCHMARK.md")
REPORT_JSON = os.path.join(ROOT_DIR, "docs/audits/MULTILANG_18432D_SIDE_BY_SIDE_BENCHMARK.json")

def run_cmd(cmd, cwd):
    print(f"  [BUILD/RUN] Executing: {' '.join(cmd)} in {cwd}")
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"❌ Command failed: {res.stderr}")
        sys.exit(1)
    return (res.stdout + "\n" + res.stderr).strip()

def main():
    print("=" * 80)
    print("  XORAS 5-LANGUAGE SIDE-BY-SIDE BARE-METAL BENCHMARK MATRIX")
    print("  Target: 100,000 18,432-D Nodes (7.37 GB Vector Memory) across 10 M4 Cores")
    print("========================================================================\n")

    results = []

    # 1. Compile C++20
    cpp_bin = os.path.join(CPP_DIR, "bench_cpp")
    run_cmd(["clang++", "-O3", "-std=c++20", "-march=armv8.5-a", "bench_18432d.cpp", "-o", cpp_bin], CPP_DIR)

    # 2. Compile Go
    go_bin = os.path.join(GO_DIR, "bench_go")
    run_cmd(["/opt/homebrew/bin/go", "build", "-o", go_bin, "bench_18432d.go"], GO_DIR)

    # 3. Compile Zig
    zig_bin = os.path.join(ZIG_DIR, "bench_18432d")
    run_cmd(["/opt/homebrew/bin/zig", "build-exe", "-O", "ReleaseFast", "bench_18432d.zig"], ZIG_DIR)

    # 4. Compile SOVRA C
    sovra_bin = os.path.join(SOVRA_DIR, "bench_sovra")
    run_cmd(["clang", "-O3", "-march=armv8.5-a", "bench_18432d.c", "-o", sovra_bin], SOVRA_DIR)

    # 5. Build Rust Cargo
    run_cmd(["cargo", "build", "--release"], RUST_DIR)
    rust_bin = os.path.join(RUST_DIR, "target/release/hexological_18432d_engine")

    # 6. Compile STREAM Hardware Baseline
    stream_bin = os.path.join(BASE_DIR, "mem_copy_baseline")
    run_cmd(["clang", "-O3", "-march=armv8.5-a", "mem_copy_baseline.c", "-o", stream_bin], BASE_DIR)

    print("\n🔥 RUNNING BARE-METAL BENCHMARK MATRIX ACROSS ALL 5 RUNTIMES...\n")

    targets = [
        ("M4 Hardware STREAM Baseline", [stream_bin], BASE_DIR),
        ("SOVRA C/NEON", [sovra_bin], SOVRA_DIR),
        ("C++20 (clang++)", [cpp_bin], CPP_DIR),
        ("Rust 1.95 (Cargo)", [rust_bin, "--json"], RUST_DIR),
        ("Zig (ReleaseFast)", [zig_bin], ZIG_DIR),
        ("Go (go build)", [go_bin], GO_DIR)
    ]

    for name, cmd, cwd in targets:
        print(f"  [RUNNING] {name}...")
        res_str = run_cmd(cmd, cwd)
        try:
            json_start = res_str.find("{")
            json_end = res_str.rfind("}") + 1
            data = json.loads(res_str[json_start:json_end])
            results.append(data)
        except Exception as e:
            print(f"❌ Failed to parse JSON output from {name}: {e}")
            print(f"Raw Output:\n{res_str}")

    # Generate Markdown Report Table
    print("\n" + "=" * 80)
    print("  SIDE-BY-SIDE BENCHMARK MATRIX RESULTS")
    print("=" * 80 + "\n")

    md_lines = []
    md_lines.append("# 🏆 XORAS 5-LANGUAGE SIDE-BY-SIDE BARE-METAL BENCHMARK REPORT\n")
    md_lines.append("> **Workload**: 100,000 18,432-D Hexological Vector Nodes (7.37 GB Vector Data)")
    md_lines.append("> **Substrate**: Apple Silicon M4 Bare Metal (`aarch64-apple-darwin`, 10 CPU Cores)")
    md_lines.append(f"> **Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n")
    md_lines.append("| Language Runtime | Execution Time | Vector Throughput | GFLOPS (ARM64) | Memory Bandwidth | p50 Latency | p99 Latency |")
    md_lines.append("|---|---|---|---|---|---|---|")

    for r in results:
        lang = r.get("language", r.get("benchmark", "Unknown"))
        ms = r.get("avg_pass_ms", r.get("elapsed_ms", 0.0))
        ops = r.get("evals_per_sec", 0.0)
        gflops = r.get("gflops", 0.0)
        gb = r.get("bandwidth_gb_sec", r.get("effective_dram_bandwidth_gb_sec", 0.0))
        p50 = r.get("p50_us", 0.0)
        p99 = r.get("p99_us", 0.0)

        line = f"| **{lang}** | `{ms:.2f} ms` | `{ops:,.0f} evals/sec` | `{gflops:,.2f} GFLOPS` | `{gb:,.2f} GB/s` | `{p50:.2f} µs` | `{p99:.2f} µs` |"
        print(line)
        md_lines.append(line)

    print("\n" + "=" * 80)

    # Save outputs
    os.makedirs(os.path.dirname(REPORT_MD), exist_ok=True)
    with open(REPORT_MD, "w") as f:
        f.write("\n".join(md_lines) + "\n")

    with open(REPORT_JSON, "w") as f:
        json.dump(results, f, indent=2)

    print(f"[+] Multi-Language Benchmark Report saved to:\n    MD:   {REPORT_MD}\n    JSON: {REPORT_JSON}")

if __name__ == "__main__":
    main()
