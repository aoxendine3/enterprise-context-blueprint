import json
import math
import hashlib
from datetime import datetime, timezone
from pathlib import Path

OUTPUT_DIR = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/scratch")
RECEIPT_FILE = OUTPUT_DIR / "BBQ_002_FFM_OPTICAL_RECEIPT.json"
MERKLE_DIR = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/tri_brain/merkle_registry")

def run_exact_bounded_matrix():
    print("\n=================================================================")
    print("BBQ-002 EXACT BOUNDED SENSITIVITY SWEEP (FFM Optical Cascade)")
    print("=================================================================")
    
    # Sensitivity matrix: Photonic laser power (mW) vs Neural Network Depth (Layers)
    power_mw_range = [1.0, 10.0, 50.0, 100.0]
    depth_layers = list(range(1, 16))
    
    results = []
    inf_snr = 999999.0
    sup_snr = -999999.0
    
    print(f"{'Input P (mW)':<12} | {'Layer Depth':<12} | {'Shot Noise (dB)':<15} | {'Final SNR (dB)':<15} | {'Status'}")
    print("-" * 75)
    
    for p_in in power_mw_range:
        for L in depth_layers:
            # Base SNR scales with log of input power
            # Shot noise accumulates non-linearly per optical layer conversion
            snr_base = 60.0 + 10.0 * math.log10(p_in)
            # Each layer introduces a Mach-Zehnder coupling loss + shot noise
            loss_per_layer = 4.5 + (1.2 * math.log10(L))
            snr_final = snr_base - (L * loss_per_layer)
            
            if snr_final < inf_snr: inf_snr = snr_final
            if snr_final > sup_snr: sup_snr = snr_final
            
            gate_pass = snr_final >= 15.0 # 15 dB minimum for basic ML inference
            status = "PASS" if gate_pass else "FAIL (DEGRADED)"
            
            results.append({
                "power_mw": p_in,
                "layer_depth": L,
                "snr_final_db": round(snr_final, 4),
                "clears_snr_gate": gate_pass
            })
            
            print(f"{p_in:<12.1f} | {L:<12d} | {loss_per_layer:<15.2f} | {snr_final:<15.2f} | {status}")
            
    # Find absolute layer limit even at max power
    max_power_results = [r for r in results if r["power_mw"] == 100.0]
    max_layer_pass = max([r["layer_depth"] for r in max_power_results if r["clears_snr_gate"]], default=0)
    
    gate_shallow_edge = max_layer_pass >= 5
    gate_deep_learning = max_layer_pass >= 50
    
    verdict = "QUALIFIED FOR SHALLOW EDGE AI ONLY" if gate_shallow_edge else "KILLED"
    taint_state = "0xBEAF0000" if gate_shallow_edge else "0xDEAD0000"
    
    receipt = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "candidate_id": "BBQ-002",
        "title": "Fully Forward Mode (FFM) Optical Training",
        "benchmark_engine": "v3.2.0-SOVEREIGN-EXACT-BOUNDED",
        "exact_bounded_metrics": {
            "infimum_snr_db": round(inf_snr, 8),
            "supremum_snr_db": round(sup_snr, 8),
            "absolute_max_layer_depth": max_layer_pass
        },
        "gates_evaluated": {
            "shallow_edge_5_layers_passed": gate_shallow_edge,
            "deep_learning_50_layers_passed": gate_deep_learning
        },
        "verdict": verdict,
        "taint_state": taint_state,
        "raw_matrix": results
    }
    
    receipt_raw = json.dumps(receipt, sort_keys=True)
    receipt_sha = hashlib.sha256(receipt_raw.encode("utf-8")).hexdigest()
    receipt["receipt_sha256"] = receipt_sha
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RECEIPT_FILE.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    
    merkle_node = {
        "file": str(RECEIPT_FILE),
        "hash": receipt_sha,
        "timestamp": receipt["timestamp"],
        "status": "bbq_gauntlet_ingestion",
        "taint": taint_state
    }
    MERKLE_DIR.mkdir(parents=True, exist_ok=True)
    (MERKLE_DIR / f"bbq_002_ffm_{receipt_sha[:8]}.json").write_text(json.dumps(merkle_node, indent=2))
    
    print("\n--- EXACT BOUNDED GATE EVALUATION ---")
    print(f"1. Shallow Edge Viability (5 Layers)  : [{'PASS' if gate_shallow_edge else 'FAIL (KILL)'}]")
    print(f"2. Deep Learning Viability (50 Layers): [{'PASS' if gate_deep_learning else 'FAIL (KILL)'}]")
    print("-----------------------------------------------------------------")
    print(f"Final Window Verdict             : {verdict}")
    print(f"Absolute Layer Ceiling           : {max_layer_pass} Layers")
    print(f"Taint State                      : {taint_state}")
    print(f"[RECEIPT SHA-256]                : {receipt_sha}")
    print("=================================================================")

if __name__ == "__main__":
    run_exact_bounded_matrix()
