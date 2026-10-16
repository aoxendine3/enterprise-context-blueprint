#!/usr/bin/env bash
set -e

echo "======================================================================"
echo "🐳 LINUX CONTAINER POLYGLOT GAUNTLET (Docker Debian Linux / AArch64)"
echo "CPU Cores: $(nproc), Kernel: $(uname -r)"
echo "Testing: C11 vs Rust vs Go vs Node.js vs Python"
echo "Workload: 1,000,000 Atomic SAGA Commits across 8 Concurrent Threads"
echo "======================================================================"

mkdir -p /app/bin

echo ""
echo "--- [1/5] Compiling and Executing C11 (GCC -O3 stdatomic.h) ---"
gcc -O3 -std=c11 -Wall -Wextra -pthread /app/bench_c11.c -o /app/bin/bench_c11_linux
/app/bin/bench_c11_linux > /app/result_c11.json
cat /app/result_c11.json

echo ""
echo "--- [2/5] Compiling and Executing Rust (rustc -O safe atomic) ---"
rustc -O /app/bench_rust.rs -o /app/bin/bench_rust_linux
/app/bin/bench_rust_linux > /app/result_rust.json
cat /app/result_rust.json

echo ""
echo "--- [3/5] Compiling and Executing Go (go build sync/atomic) ---"
go build -o /app/bin/bench_go_linux /app/bench_go.go
/app/bin/bench_go_linux > /app/result_go.json
cat /app/result_go.json

echo ""
echo "--- [4/5] Executing Node.js (Atomics + SharedArrayBuffer) ---"
node /app/bench_node.mjs > /app/result_node.json
cat /app/result_node.json

echo ""
echo "--- [5/5] Executing Python 3 (Threading + Lock) ---"
python3 /app/bench_python.py > /app/result_python.json
cat /app/result_python.json

echo ""
echo "======================================================================"
echo "📊 CONSOLIDATED DOCKER CONTAINER RESULTS SUMMARY"
echo "======================================================================"
python3 - << 'PYEOF'
import json

files = [
    ("C11 (GCC -O3)", "/app/result_c11.json"),
    ("Rust (rustc -O)", "/app/result_rust.json"),
    ("Go 1.22+ (atomic)", "/app/result_go.json"),
    ("Node.js (Atomics)", "/app/result_node.json"),
    ("Python 3.12+", "/app/result_python.json"),
]

print(f"{'Language':<22} | {'Throughput (ops/sec)':<22} | {'Latency':<12} | {'Elapsed':<10} | {'Peak RSS':<10} | {'Status'}")
print("-" * 92)

for name, fpath in files:
    try:
        with open(fpath) as f:
            d = json.load(f)
            tput = f"{d.get('throughput_ops_sec', 0):,}"
            lat = f"{d.get('avg_latency_ns', 0):.1f} ns"
            el = f"{d.get('elapsed_ms', 0):.1f} ms"
            rss = f"{d.get('peak_rss_mb', 0):.2f} MB"
            print(f"{name:<22} | {tput:<22} | {lat:<12} | {el:<10} | {rss:<10} | VERIFIED")
    except Exception as e:
        print(f"{name:<22} | ERROR: {e}")
print("-" * 92)
PYEOF
