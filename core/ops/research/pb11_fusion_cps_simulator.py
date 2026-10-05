import json
import math
import hashlib
from datetime import datetime, timezone
from pathlib import Path

# Paths
OUTPUT_DIR = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/scratch")
RECEIPT_FILE = OUTPUT_DIR / "BBQ_001_PB11_RECEIPT.json"
MERKLE_DIR = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/tri_brain/merkle_registry")

class PB11FusionCPS:
    def __init__(self, T_i_keV, Te_ratio):
        self.T_i = T_i_keV
        self.T_e = T_i_keV / Te_ratio
        self.Z_eff = 2.5 # Effective charge for p-B11 plasma
        
    def calculate_bremsstrahlung(self):
        # P_brems ~ C * Z_eff^2 * n_e * n_i * sqrt(T_e)
        # Simplified normalized model for the gauntlet
        return 5.35 * (self.Z_eff**2) * math.sqrt(self.T_e)

    def calculate_fusion_power(self):
        # Reactivity <sigma v> peaks strongly at 600 keV for p-B11
        if self.T_i < 100:
            return 0.0
        reactivity = math.exp(-((self.T_i - 600)**2) / 45000)
        return 180.0 * reactivity

    def solve_equilibrium(self):
        p_fus = self.calculate_fusion_power()
        p_rad = self.calculate_bremsstrahlung()
        net = p_fus - p_rad
        return {
            "T_i_keV": self.T_i,
            "T_e_keV": self.T_e,
            "p_fusion_mw": p_fus,
            "p_brems_mw": p_rad,
            "net_power_mw": net,
            "ignition": net > 0
        }

def run_exact_bounded_matrix():
    print("\n=================================================================")
    print("BBQ-001 EXACT BOUNDED SENSITIVITY SWEEP (Aneutronic p-B11 Fusion)")
    print("=================================================================")
    
    T_i_range = [300.0, 400.0, 491.9, 500.0, 600.0, 700.0, 800.0]
    Te_ratios = [1.0, 1.5, 2.0, 2.5] # Ti/Te ratio. If 1.0, thermal equilibrium.
    
    results = []
    inf_net_power = 999999.0
    sup_net_power = -999999.0
    ignition_count = 0
    
    print(f"{'T_i (keV)':<10} | {'T_i/T_e Ratio':<14} | {'T_e (keV)':<10} | {'P_fus (MW)':<10} | {'P_rad (MW)':<10} | {'Net (MW)':<10} | {'Status'}")
    print("-" * 85)
    
    for ti in T_i_range:
        for ratio in Te_ratios:
            sim = PB11FusionCPS(T_i_keV=ti, Te_ratio=ratio)
            sol = sim.solve_equilibrium()
            
            if sol["net_power_mw"] < inf_net_power:
                inf_net_power = sol["net_power_mw"]
            if sol["net_power_mw"] > sup_net_power:
                sup_net_power = sol["net_power_mw"]
                
            if sol["ignition"]:
                ignition_count += 1
                status = "PASS (IGNITION)"
            else:
                status = "FAIL (COLLAPSE)"
                
            results.append({
                "T_i_keV": ti,
                "Te_ratio": ratio,
                "T_e_keV": round(sol["T_e_keV"], 2),
                "P_fusion_mw": round(sol["p_fusion_mw"], 4),
                "P_rad_mw": round(sol["p_brems_mw"], 4),
                "Net_power_mw": round(sol["net_power_mw"], 4),
                "clears_ignition_gate": sol["ignition"]
            })
            
            print(f"{ti:<10.1f} | {ratio:<14.2f} | {sol['T_e_keV']:<10.2f} | {sol['p_fusion_mw']:<10.2f} | {sol['p_brems_mw']:<10.2f} | {sol['net_power_mw']:<10.2f} | {status}")

    # Gates Evaluation
    gate_thermal_eq = any(r["clears_ignition_gate"] for r in results if r["Te_ratio"] == 1.0)
    gate_non_thermal = any(r["clears_ignition_gate"] for r in results if r["Te_ratio"] >= 2.0)
    
    verdict = "QUALIFIED UNDER NON-THERMAL BOUNDS" if gate_non_thermal and not gate_thermal_eq else "KILLED (IMPOSSIBLE)"
    taint_state = "0xBEAF0000" if gate_non_thermal else "0xDEAD0000"
    
    receipt = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "candidate_id": "BBQ-001",
        "title": "Aneutronic p-B11 Fusion Plasma",
        "benchmark_engine": "v3.2.0-SOVEREIGN-EXACT-BOUNDED",
        "exact_bounded_metrics": {
            "infimum_net_power_mw": round(inf_net_power, 8),
            "supremum_net_power_mw": round(sup_net_power, 8),
            "total_matrices_evaluated": len(results),
            "ignition_regimes_found": ignition_count
        },
        "gates_evaluated": {
            "thermal_equilibrium_survival_passed": gate_thermal_eq,
            "non_thermal_hot_ion_survival_passed": gate_non_thermal
        },
        "verdict": verdict,
        "taint_state": taint_state,
        "raw_matrix": results
    }
    
    receipt_raw = json.dumps(receipt, sort_keys=True)
    receipt_sha = hashlib.sha256(receipt_raw.encode("utf-8")).hexdigest()
    receipt["receipt_sha256"] = receipt_sha
    
    # Save receipt
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RECEIPT_FILE.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    
    # Save to Merkle Registry
    merkle_node = {
        "file": str(RECEIPT_FILE),
        "hash": receipt_sha,
        "timestamp": receipt["timestamp"],
        "status": "bbq_gauntlet_ingestion",
        "taint": taint_state
    }
    MERKLE_DIR.mkdir(parents=True, exist_ok=True)
    merkle_path = MERKLE_DIR / f"bbq_001_pb11_{receipt_sha[:8]}.json"
    merkle_path.write_text(json.dumps(merkle_node, indent=2))
    
    print("\n--- EXACT BOUNDED GATE EVALUATION ---")
    print(f"1. Thermal Equilibrium (Ti = Te) Ignition : [{'PASS' if gate_thermal_eq else 'FAIL (KILL)'}]")
    print(f"2. Hot-Ion Non-Thermal (Ti > 2Te) Ignition: [{'PASS' if gate_non_thermal else 'FAIL (KILL)'}]")
    print("-----------------------------------------------------------------")
    print(f"Final Window Verdict             : {verdict}")
    print(f"Taint State                      : {taint_state}")
    print(f"[RECEIPT SHA-256]                : {receipt_sha}")
    print("=================================================================")

if __name__ == "__main__":
    run_exact_bounded_matrix()
