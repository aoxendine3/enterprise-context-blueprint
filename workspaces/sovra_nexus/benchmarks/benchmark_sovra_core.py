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
from sovra_core.mast_taxonomy import MASTTaxonomy
from sovra_core.pyramidal_distillation import PyramidalDistillationEngine

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

def benchmark_mast_taxonomy(iterations=20000):
    mast = MASTTaxonomy()
    telemetry = {"timeout_ratio": 0.05, "duplicate_utterance_ratio": 0.02, "memory_saturation": 0.45}
    start = time.perf_counter()
    for _ in range(iterations):
        _ = mast.evaluate(telemetry)
    elapsed = time.perf_counter() - start
    ops_sec = iterations / elapsed
    ns_per_op = (elapsed / iterations) * 1e9
    print(f"[BENCHMARK] MAST Safety Evaluation (14 Failure Modes): {iterations:,} evals in {elapsed:.4f}s ({ops_sec:,.0f} ops/sec, {ns_per_op:.2f} ns/op)")
    return ops_sec

def benchmark_pyramidal_distillation(iterations=500):
    engine = PyramidalDistillationEngine()
    raw_24 = [
        {"id": f"src_{i:02d}", "domain": f"domain_{i % 6}", "content": f"High entropy signal {i} with metrics and telemetry", "score": 0.5 + (i * 0.01)}
        for i in range(24)
    ]
    start = time.perf_counter()
    for _ in range(iterations):
        _ = engine.distill(raw_24)
    elapsed = time.perf_counter() - start
    ops_sec = iterations / elapsed
    ms_per_op = (elapsed / iterations) * 1000.0
    print(f"[BENCHMARK] 24/12/7/3/1 Pyramidal Distillation: {iterations:,} cycles in {elapsed:.4f}s ({ops_sec:,.0f} cycles/sec, {ms_per_op:.3f} ms/cycle)")
    return ops_sec

if __name__ == "__main__":
    print("=" * 70)
    print("  XORAS SOVRA CORE BARE-METAL HARDWARE BENCHMARK")
    print("=" * 70)
    benchmark_poincare()
    benchmark_hexcell_io()
    benchmark_streaming_entropy()
    benchmark_kernel_drift()
    benchmark_mast_taxonomy()
    benchmark_pyramidal_distillation()
    print("=" * 70)
