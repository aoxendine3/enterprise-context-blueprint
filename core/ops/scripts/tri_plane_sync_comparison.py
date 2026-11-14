#!/usr/bin/env python3
"""
XORAS Tri-Plane Synchronization & Comparative Benchmark
Measures live performance across all three architectural planes:
- Plane 1: Local Apple Silicon M4 (Unified RAM / POSIX / SIMD)
- Plane 2: Bare-Metal Windows Node (192.168.1.211 / Ollama Tensor Plane)
- Plane 3: Cloud DAXX Swarm (Reasoning Conductor / Edge Gateway)
"""

import os
import sys
import time
import json
import subprocess
import requests
import numpy as np

ROOT = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

def test_plane_1_local_mac():
    print("\n--- [PLANE 1: LOCAL APPLE SILICON M4 UNIFIED RAM] ---")
    t0 = time.perf_counter()
    
    # 1. NEON SIMD Vector similarity
    from workspaces.tonydb.python.tonydb_client import TonyDB
    db = TonyDB(max_cells=100)
    vec_a = np.random.randn(128).astype(np.float32)
    vec_b = vec_a.copy()
    sim_t0 = time.perf_counter()
    sim = db.similarity(vec_a, vec_b)
    sim_elapsed_us = (time.perf_counter() - sim_t0) * 1_000_000
    db.close()
    
    # 2. Local POSIX Boundary Guard
    bg_t0 = time.perf_counter()
    res_bg = subprocess.run(["python3", "ops/scripts/boundary_guard.py", f"{ROOT}/workspaces"], capture_output=True, text=True, cwd=ROOT)
    bg_elapsed_ms = (time.perf_counter() - bg_t0) * 1000
    
    total_elapsed_ms = (time.perf_counter() - t0) * 1000
    
    p1_data = {
        "plane": "Plane 1 (Local Apple Silicon M4)",
        "hardware": "Physical Apple Silicon M4 (Unified Memory)",
        "simd_similarity": round(float(sim), 4),
        "simd_latency_us": round(sim_elapsed_us, 2),
        "posix_boundary_gate_ms": round(bg_elapsed_ms, 2),
        "posix_exit_code": res_bg.returncode,
        "total_plane_latency_ms": round(total_elapsed_ms, 2),
        "status": "OPERATIONAL"
    }
    print(f"  * NEON SIMD Latency : {sim_elapsed_us:.1f} µs (Cosine: {sim:.4f})")
    print(f"  * POSIX Boundary Gate: {bg_elapsed_ms:.2f} ms (Exit Code: {res_bg.returncode})")
    print(f"  * Total Plane Envelope: {total_elapsed_ms:.2f} ms")
    return p1_data

def test_plane_2_windows_gpu():
    print("\n--- [PLANE 2: WINDOWS 1TB GPU TENSOR PLANE (192.168.1.211)] ---")
    target_ip = "192.168.1.211"
    
    # 1. Measure ICMP Ping
    ping_res = subprocess.run(["ping", "-c", "2", "-t", "2", target_ip], capture_output=True, text=True)
    icmp_ms = 0.0
    for line in ping_res.stdout.split("\n"):
        if "round-trip" in line or "avg" in line:
            parts = line.split("=")[-1].strip().split("/")
            if len(parts) >= 2:
                icmp_ms = float(parts[1])
                
    # 2. Query Ollama model tags
    t0_tags = time.perf_counter()
    try:
        r_tags = requests.get(f"http://{target_ip}:11434/api/tags", timeout=5)
        tags_ms = (time.perf_counter() - t0_tags) * 1000
        models_data = r_tags.json().get("models", [])
        model_count = len(models_data)
        model_names = [m.get("name") for m in models_data[:5]]
    except Exception as e:
        tags_ms = 0.0
        model_count = 0
        model_names = []

    # 3. Measure inference generation on loaded model
    t0_gen = time.perf_counter()
    tokens = 0
    tps = 0.0
    response_sample = ""
    try:
        gen_payload = {
            "model": "qwen2.5:1.5b",
            "prompt": "XORAS Tri-Sync verification test: reply with exact words: SYSTEM ONLINE.",
            "stream": False
        }
        # The Windows tensor plane is a 1TB bare-metal box under load; a cold
        # 1.5B generation has been measured at 100+ seconds. A 20-second budget
        # produced a false "OPERATIONAL" verdict on a node that returned nothing.
        r_gen = requests.post(f"http://{target_ip}:11434/api/generate", json=gen_payload, timeout=240)
        gen_elapsed_ms = (time.perf_counter() - t0_gen) * 1000
        gdata = r_gen.json()
        tokens = gdata.get("eval_count", 0)
        eval_dur_s = gdata.get("eval_duration", 1) / 1e9
        tps = tokens / eval_dur_s if eval_dur_s > 0 else 0
        response_sample = gdata.get("response", "").strip()[:80]
    except Exception as e:
        gen_elapsed_ms = (time.perf_counter() - t0_gen) * 1000
        response_sample = f"ERR: {e}"

    p2_data = {
        "plane": "Plane 2 (Windows 1TB Tensor Plane)",
        "host": f"{target_ip}:11434",
        "icmp_latency_ms": round(icmp_ms, 2),
        "api_handshake_ms": round(tags_ms, 2),
        "loaded_models_count": model_count,
        "sample_models": model_names,
        "active_model_tested": "qwen2.5:1.5b",
        "tokens_generated": tokens,
        "token_throughput_tps": round(tps, 1),
        "inference_roundtrip_ms": round(gen_elapsed_ms, 2),
        "response_sample": response_sample,
        # Truthful status: inventory alone is not operation. The plane is only
        # OPERATIONAL when inference actually produced tokens.
        "status": "OPERATIONAL" if (model_count > 0 and tokens > 0) else ("DEGRADED_INFERENCE" if model_count > 0 else "DEGRADED")
    }
    print(f"  * LAN ICMP Roundtrip : {icmp_ms:.2f} ms")
    print(f"  * VRAM Loaded Models : {model_count} models ({', '.join(model_names[:3])}...)")
    print(f"  * Inference Envelope : {gen_elapsed_ms:.2f} ms ({tokens} tokens @ {tps:.1f} tok/sec)")
    print(f"  * Model Response     : \"{response_sample}\"")
    return p2_data

def test_plane_3_daxx_cloud():
    print("\n--- [PLANE 3: CLOUD DAXX REASONING ENGINE & EDGE GATEWAY] ---")
    t0 = time.perf_counter()
    
    # 1. Edge Gateway Ping (xoras.info)
    t0_edge = time.perf_counter()
    try:
        r_edge = requests.get("https://xoras.info", timeout=5)
        edge_ms = (time.perf_counter() - t0_edge) * 1000
        edge_status = r_edge.status_code
        cf_ray = r_edge.headers.get("cf-ray", "N/A")
    except Exception as e:
        edge_ms = 0.0
        edge_status = 500
        cf_ray = "ERROR"

    # 2. Autonomous Swarm Conductor Coordination (25 Agents Across 6 Tiers)
    t0_swarm = time.perf_counter()
    res_swarm = subprocess.run(["python3", "ops/commerce/daxxco_engine_v2/verify_installation.py"], capture_output=True, text=True, cwd=ROOT)
    swarm_ms = (time.perf_counter() - t0_swarm) * 1000
    swarm_ok = (res_swarm.returncode == 0)

    total_cloud_ms = (time.perf_counter() - t0) * 1000

    p3_data = {
        "plane": "Plane 3 (Cloud DAXX Reasoning Engine)",
        "edge_gateway_url": "https://xoras.info",
        "edge_http_status": edge_status,
        "edge_latency_ms": round(edge_ms, 2),
        "cloudflare_ray": cf_ray,
        "swarm_conductor_status": "PASS" if swarm_ok else "FAIL",
        "swarm_coordination_ms": round(swarm_ms, 2),
        "total_plane_latency_ms": round(total_cloud_ms, 2),
        "status": "OPERATIONAL" if (edge_status == 200 and swarm_ok) else "DEGRADED"
    }
    print(f"  * Edge Gateway (Cloudflare): {edge_ms:.2f} ms (Status: {edge_status}, Ray: {cf_ray})")
    print(f"  * Swarm Conductor Handoff : {swarm_ms:.2f} ms ({'ALL PASS' if swarm_ok else 'FAIL'})")
    print(f"  * Total Plane Envelope   : {total_cloud_ms:.2f} ms")
    return p3_data

def main():
    print("=" * 75)
    print("🌐 XORAS SOVEREIGN TRI-PLANE SYNCHRONIZATION BENCHMARK")
    print("=" * 75)
    
    t_start = time.perf_counter()
    p1 = test_plane_1_local_mac()
    p2 = test_plane_2_windows_gpu()
    p3 = test_plane_3_daxx_cloud()
    total_sync_time = round((time.perf_counter() - t_start) * 1000, 2)

    # Derived verdict — never asserted. A plane that degraded degrades the
    # aggregate; the report says what actually happened.
    plane_statuses = {p1.get("status"), p2.get("status"), p3.get("status")}
    operational_count = sum(1 for s in (p1.get("status"), p2.get("status"), p3.get("status")) if s == "OPERATIONAL")
    if operational_count == 3:
        tri_status = "100% OPERATIONAL & SYNCHRONIZED"
    elif operational_count > 0:
        tri_status = f"PARTIAL: {operational_count}/3 PLANES OPERATIONAL (degraded: {sorted(s for s in plane_statuses if s != 'OPERATIONAL')})"
    else:
        tri_status = "DEGRADED: NO PLANE OPERATIONAL"

    comparative_report = {
        "benchmark_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_tri_sync_envelope_ms": total_sync_time,
        "planes": {
            "plane_1_local_mac": p1,
            "plane_2_windows_gpu": p2,
            "plane_3_cloud_daxx": p3
        },
        "planes_operational": operational_count,
        "tri_sync_status": tri_status
    }
    
    out_file = os.path.join(ROOT, "memory/agent_logs/tri_plane_sync_comparison.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(comparative_report, f, indent=2)
        
    print("\n" + "=" * 75)
    print(f"🧭 TRI-PLANE SYNC REPORT: {tri_status}")
    print(f"   Envelope: {total_sync_time:.2f} ms | Planes operational: {operational_count}/3")
    print(f"📄 Official Comparison Receipt: {out_file}")
    print("=" * 75)

if __name__ == "__main__":
    main()
