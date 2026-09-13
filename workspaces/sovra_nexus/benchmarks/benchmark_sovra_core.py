"""
XORAS SOVRA CORE: BARE-METAL EMPIRICAL BENCHMARK
Measures operational throughput, latency, and cache efficiency.
"""

import math
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sovra_core.poincare_hypergraph import PoincareManifold
from sovra_core.hexcell_memory import HexCell, HexCellEngine
from sovra_core.streaming_entropy import StreamingEntropyEngine
from sovra_core.kernel_drift_detector import KernelDriftDetector

def benchmark_poincare(iterations=50000):
    manifold = PoincareManifold(dim=16)
    u = [0.1 * math.sin(i) for i in range(16)]
    v = [0.1 * math.cos(i) for i in range(16)]

    start = time.perf_counter()
    for _ in range(iterations):
        _ = manifold.geodesic_distance(u, v)
    elapsed = time.perf_counter() - start

    ops_sec = iterations / elapsed
    ns_per_op = (elapsed / iterations) * 1e9
    print(f"[BENCHMARK] Poincare Distance: {iterations:,} ops in {elapsed:.4f}s ({ops_sec:,.0f} ops/sec, {ns_per_op:.2f} ns/op)")
    return ops_sec

def benchmark_hexcell_io(iterations=25000):
    engine = HexCellEngine(capacity=1000)
    sample_cell = HexCell(cell_id=99, flags=1, payload=b"BENCHMARK_PAYLOAD_TEST")

    start = time.perf_counter()
    for i in range(iterations):
        sample_cell.cell_id = i
        idx = engine.write_cell(sample_cell)
        _ = engine.read_cell(idx)
    elapsed = time.perf_counter() - start

    ops_sec = iterations / elapsed
    ns_per_op = (elapsed / iterations) * 1e9
    print(f"[BENCHMARK] 3200-Byte HexCell Read/Write: {iterations:,} roundtrips in {elapsed:.4f}s ({ops_sec:,.0f} ops/sec, {ns_per_op:.2f} ns/op)")
    return ops_sec

def benchmark_streaming_entropy(iterations=100000):
    engine = StreamingEntropyEngine()
    test_token = "x4kP9zL2mNqR5wT8vB1jY6cH3sG0vF9d"

    start = time.perf_counter()
    for _ in range(iterations):
        _ = engine.calculate_entropy(test_token)
    elapsed = time.perf_counter() - start

    ops_sec = iterations / elapsed
    ns_per_op = (elapsed / iterations) * 1e9
    print(f"[BENCHMARK] Streaming Entropy (LUT): {iterations:,} tokens in {elapsed:.4f}s ({ops_sec:,.0f} ops/sec, {ns_per_op:.2f} ns/op)")
    return ops_sec

def benchmark_kernel_drift():
    detector = KernelDriftDetector(str(Path(__file__).resolve().parent.parent))
    start = time.perf_counter()
    digest, count = detector.snapshot()
    elapsed = time.perf_counter() - start
    print(f"[BENCHMARK] Kernel Drift Snapshot: {count} files fingerprinted in {elapsed * 1000:.2f}ms (Root: {digest[:16]}...)")

if __name__ == "__main__":
    print("=" * 70)
    print("  XORAS SOVRA CORE BARE-METAL HARDWARE BENCHMARK")
    print("=" * 70)
    benchmark_poincare()
    benchmark_hexcell_io()
    benchmark_streaming_entropy()
    benchmark_kernel_drift()
    print("=" * 70)
