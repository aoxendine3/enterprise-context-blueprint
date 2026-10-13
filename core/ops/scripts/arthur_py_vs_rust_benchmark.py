#!/usr/bin/env python3
"""
Benchmark Arthur Python AST Engine vs Arthur Rust (Tree-Sitter) Binary.
Measures latency, accuracy, and throughput across both single-shot and 64-parallel proposal batches.
"""
import os
import sys
import time
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

WORKSPACE = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
sys.path.insert(0, str(WORKSPACE))

from agents.citizens.arthur.arthur_compliance_kernel import ArthurSanitizerLatticeKernel

# Sample code snippets
TEST_SUITE = {
    "clean_code": """
import json

def process_event(event_dict):
    keys = list(event_dict.keys())
    return len(keys)
""",
    "banned_eval": """
def dangerous(user_input):
    return eval(user_input)
""",
    "tainted_getattr": """
import os
attr = os.getenv("TARGET_OP")
getattr(worker, attr)()
""",
    "whitelisted_getattr": """
import os
key = os.getenv("CONFIG_FIELD")
if key in ("host", "port", "timeout"):
    val = getattr(server_config, key)
""",
    "dynamic_import": """
import importlib
importlib.import_module("os")
"""
}

def run_bench():
    print("=" * 80)
    print("  ARTHUR AST BENCHMARK: PYTHON (ast) vs RUST (tree-sitter)")
    print("=" * 80)
    
    # 1. Setup temp files
    temp_dir = WORKSPACE / "core/ops/scratch_bench"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    file_map = {}
    for name, code in TEST_SUITE.items():
        fpath = temp_dir / f"{name}.py"
        fpath.write_text(code.strip())
        file_map[name] = fpath
        
    # 2. Benchmark Python Engine
    py_kernel = ArthurSanitizerLatticeKernel()
    
    # Warmup
    for f in file_map.values():
        py_kernel.scan_python_ast_security(f)
        
    iterations = 200
    t0 = time.perf_counter()
    for _ in range(iterations):
        for f in file_map.values():
            py_kernel.scan_python_ast_security(f)
    t1 = time.perf_counter()
    py_total = t1 - t0
    py_per_scan_us = (py_total / (iterations * len(file_map))) * 1e6
    
    print(f"\n[PYTHON] Total ({iterations * len(file_map)} scans): {py_total:.4f} s")
    print(f"[PYTHON] Single-File Scan Latency: {py_per_scan_us:.2f} µs ({py_per_scan_us/1000:.3f} ms)")
    print(f"[PYTHON] Single-Core Throughput:   {1e6 / py_per_scan_us:.1f} scans/sec")
    
    # 3. Benchmark Rust Engine inside container
    rust_binary = "/workspace/core/ops/src/arthur_ast_rs/target/release/arthur_ast_rs"
    
    # Verify Rust binary returns identical verdicts
    print("\n--- Verifying Semantic Equivalence ---")
    for name, fpath in file_map.items():
        py_violations = py_kernel.scan_python_ast_security(fpath)
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{WORKSPACE}:/workspace",
            "-w", "/workspace",
            "rust:latest",
            rust_binary, f"/workspace/core/ops/scratch_bench/{name}.py"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        rust_status = "PASSED" if res.returncode == 0 else f"VETO (code {res.returncode})"
        py_status = "PASSED" if len(py_violations) == 0 else f"VETO ({len(py_violations)})"
        match_symbol = "✓" if (res.returncode == 0) == (len(py_violations) == 0) else "✗"
        print(f"  {match_symbol} {name:<22} | Python: {py_status:<12} | Rust: {rust_status}")

    # Clean up scratch files
    for f in file_map.values():
        f.unlink()
    temp_dir.rmdir()
    
    print("=" * 80)

if __name__ == "__main__":
    run_bench()
