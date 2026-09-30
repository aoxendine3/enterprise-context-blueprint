#!/usr/bin/env python3
"""
Sovra-Nexus Zig SIMD Engine Python Wrapper & Benchmark Suite
Provides zero-copy ctypes interop with compiled Zig SIMD dynamic library.
"""

import sys
import os
import ctypes
import time
import platform
import numpy as np
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_ROOT = SCRIPT_DIR.parent.parent.resolve()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

BUILD_DIR = SCRIPT_DIR / "build"

def _load_zig_library():
    system = platform.system().lower()
    if system == "windows":
        lib_name = "sovra_simd.dll"
    elif system == "darwin":
        lib_name = "libsovra_simd.dylib"
    else:
        lib_name = "libsovra_simd.so"

    lib_path = BUILD_DIR / lib_name

    if not lib_path.exists():
        # Attempt compilation
        print(f"[!] Library {lib_path.name} not found. Running compiler...")
        from ops.native.compile_zig import compile_zig
        lib_path = compile_zig()

    lib = ctypes.CDLL(str(lib_path))

    # Define function signatures
    # 1. sovra_simd_dot_f32
    lib.sovra_simd_dot_f32.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_size_t]
    lib.sovra_simd_dot_f32.restype = ctypes.c_float

    # 2. sovra_simd_l2_norm_f32
    lib.sovra_simd_l2_norm_f32.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_size_t]
    lib.sovra_simd_l2_norm_f32.restype = ctypes.c_float

    # 3. sovra_simd_euclidean_dist_sq_f32
    lib.sovra_simd_euclidean_dist_sq_f32.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_size_t]
    lib.sovra_simd_euclidean_dist_sq_f32.restype = ctypes.c_float

    # 4. sovra_simd_poincare_distance_f32
    lib.sovra_simd_poincare_distance_f32.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_size_t]
    lib.sovra_simd_poincare_distance_f32.restype = ctypes.c_float

    # 5. get_sovra_zig_info
    lib.get_sovra_zig_info.argtypes = []
    lib.get_sovra_zig_info.restype = ctypes.c_char_p

    return lib

try:
    _ZIG_LIB = _load_zig_library()
    _ZIG_AVAILABLE = True
except Exception as e:
    print(f"[!] Warning: Failed to load Zig SIMD library: {e}")
    _ZIG_LIB = None
    _ZIG_AVAILABLE = False

def get_zig_info() -> str:
    if _ZIG_AVAILABLE and _ZIG_LIB:
        return _ZIG_LIB.get_sovra_zig_info().decode('utf-8')
    return "Zig SIMD Engine Unavailable (Fallback Active)"

def zig_dot_f32(a: np.ndarray, b: np.ndarray) -> float:
    """Zero-copy Zig SIMD float32 dot product."""
    if not _ZIG_AVAILABLE:
        return float(np.dot(a, b))
    
    assert a.dtype == np.float32 and b.dtype == np.float32
    assert a.size == b.size

    n = a.size
    a_ptr = a.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    b_ptr = b.ctypes.data_as(ctypes.POINTER(ctypes.c_float))

    return float(_ZIG_LIB.sovra_simd_dot_f32(a_ptr, b_ptr, n))

def zig_poincare_dist_f32(u: np.ndarray, v: np.ndarray) -> float:
    """Zero-copy Zig SIMD Poincaré hyperbolic distance."""
    if not _ZIG_AVAILABLE:
        # Fallback Poincaré distance
        sq_dist = np.sum((u - v) ** 2)
        u_sq = np.sum(u ** 2)
        v_sq = np.sum(v ** 2)
        clamp_u = min(0.999999, u_sq)
        clamp_v = min(0.999999, v_sq)
        denom = (1.0 - clamp_u) * (1.0 - clamp_v)
        arg = 1.0 + (2.0 * sq_dist / denom)
        return float(np.arccosh(arg))

    assert u.dtype == np.float32 and v.dtype == np.float32
    assert u.size == v.size

    n = u.size
    u_ptr = u.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    v_ptr = v.ctypes.data_as(ctypes.POINTER(ctypes.c_float))

    return float(_ZIG_LIB.sovra_simd_poincare_distance_f32(u_ptr, v_ptr, n))

def run_empirical_benchmark():
    print("==========================================================")
    print("      SOVRA-NEXUS ZIG SIMD ENGINE EMPIRICAL BENCHMARK     ")
    print("==========================================================")
    print(f"Info: {get_zig_info()}\n")

    if not _ZIG_AVAILABLE:
        print("[-] Error: Zig SIMD Library is not loaded.")
        return

    # Benchmark 1: 1,000,000 float32 dot product
    N1 = 1_000_000
    print(f"[+] Generating {N1:,} float32 vector pairs...")
    a1 = np.random.randn(N1).astype(np.float32)
    b1 = np.random.randn(N1).astype(np.float32)

    # Correctness check
    np_dot = float(np.dot(a1, b1))
    zig_dot = zig_dot_f32(a1, b1)
    diff = abs(np_dot - zig_dot)
    rel_err = diff / abs(np_dot)
    print(f"[+] Accuracy Verification vs NumPy:")
    print(f"    NumPy Dot Result : {np_dot:.6f}")
    print(f"    Zig SIMD Result  : {zig_dot:.6f}")
    print(f"    Abs Error        : {diff:.6e}")
    print(f"    Rel Error        : {rel_err:.6e} {'[PASSED]' if rel_err < 1e-4 else '[FAILED]'}")

    # Latency & Throughput Benchmark over 500 iterations
    ITERS = 500
    print(f"\n[+] Running {ITERS} iterations benchmark on 1M floats...")
    
    t0 = time.perf_counter()
    for _ in range(ITERS):
        _ = zig_dot_f32(a1, b1)
    t1 = time.perf_counter()
    
    total_time = t1 - t0
    avg_latency_ms = (total_time / ITERS) * 1000.0
    # 2 ops per element (1 mult, 1 add)
    total_flops = 2.0 * N1 * ITERS
    gflops = (total_flops / total_time) / 1e9

    print(f"[OK] Zig SIMD Performance Metrics:")
    print(f"    Total Time       : {total_time:.4f} sec")
    print(f"    Avg Latency      : {avg_latency_ms:.4f} ms per 1M floats")
    print(f"    Throughput       : {gflops:.2f} GFLOPS")

    # Benchmark 2: Poincaré Hyperbolic Distance Benchmark (100,000 embedding dim)
    N2 = 100_000
    u_emb = (np.random.randn(N2) * 0.001).astype(np.float32)
    v_emb = (np.random.randn(N2) * 0.001).astype(np.float32)

    t0 = time.perf_counter()
    for _ in range(ITERS):
        _ = zig_poincare_dist_f32(u_emb, v_emb)
    t1 = time.perf_counter()
    
    p_time = t1 - t0
    p_latency = (p_time / ITERS) * 1000.0
    print(f"\n[OK] Poincaré Hyperbolic Metric Performance:")
    print(f"    Avg Latency      : {p_latency:.4f} ms per 100k embedding")

    print("\n==========================================================")
    print("                 BENCHMARK SWEEP COMPLETE                 ")
    print("==========================================================")

if __name__ == "__main__":
    run_empirical_benchmark()
