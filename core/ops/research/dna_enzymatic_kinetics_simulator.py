import json
import math
from datetime import datetime, timezone
from pathlib import Path

# Outputs
OUTPUT_DIR = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/scratch")
RECEIPT_FILE = OUTPUT_DIR / "DNA_KINETICS_RECEIPT.json"

class DNAKineticsSimulator:
    def __init__(self, method="Enzymatic_TdT", array_channels=1e6, temp_c=37.0):
        self.method = method
        self.array_channels = array_channels # Number of parallel spots on CMOS
        self.temp_k = temp_c + 273.15
        
        # Fundamental physical/chemical constants
        self.R = 8.314 # J/(mol*K)
        
        if self.method == "Phosphoramidite":
            self.activation_energy_j = 45000 # Typical organic coupling E_a
            self.A_factor = 1e8
            self.reagent_cost_per_cycle = 1e-4 # $ per spot
            self.cycle_time_base_sec = 120.0 # Wash/deprotect/couple/cap/ox
            self.max_length = 200 # nucleotides
        else: # Enzymatic TdT
            self.activation_energy_j = 30000 # Enzyme catalyzed E_a
            self.A_factor = 1e6
            self.reagent_cost_per_cycle = 2e-6 # Much cheaper aqueous reagents
            self.cycle_time_base_sec = 2.0 # Fast aqueous flow without harsh washing
            self.max_length = 1000 # nucleotides

    def calculate_coupling_rate(self):
        # Arrhenius eq
        k = self.A_factor * math.exp(-self.activation_energy_j / (self.R * self.temp_k))
        return k

    def solve_economics(self, target_exabytes=1.0):
        target_bytes = target_exabytes * 1e18
        bits_per_nt = 1.8 # Due to error correction overhead (2 bits max, real is ~1.8)
        total_nt_needed = (target_bytes * 8) / bits_per_nt
        
        rate_k = self.calculate_coupling_rate()
        
        # Effective time per cycle is bottlenecked by fluidics or reaction kinetics
        eff_cycle_time = max(self.cycle_time_base_sec, 1.0 / rate_k)
        
        # Write speed (nt / sec)
        global_write_speed_nt_sec = self.array_channels * (1.0 / eff_cycle_time)
        
        # Time to write
        time_to_write_sec = total_nt_needed / global_write_speed_nt_sec
        years_to_write = time_to_write_sec / (3600 * 24 * 365)
        
        # Cost
        total_cycles = total_nt_needed / self.array_channels
        total_cost_usd = total_cycles * self.array_channels * self.reagent_cost_per_cycle
        cost_per_gb = total_cost_usd / (target_bytes / 1e9)
        
        return {
            "eff_cycle_time_sec": eff_cycle_time,
            "write_speed_nt_sec": global_write_speed_nt_sec,
            "years_to_write_1_EB": years_to_write,
            "total_cost_usd_1_EB": total_cost_usd,
            "cost_per_gb_usd": cost_per_gb
        }

def run_sensitivity_matrix():
    print("\n=================================================================")
    print("BBQ-005 EXACT BOUNDED DNA SYNTHESIS SENSITIVITY SWEEP")
    print("=================================================================")
    
    channel_counts = [1e6, 1e8, 1e10] # CMOS Density progression
    temperatures = [20.0, 37.0, 50.0]
    
    results = []
    
    print(f"{'Method':<16} | {'CMOS Channels':<12} | {'Temp C':<6} | {'Time/Cycle':<10} | {'Years to 1EB':<12} | {'Cost/GB ($)':<12} | {'Status'}")
    print("-" * 100)
    
    for method in ["Phosphoramidite", "Enzymatic_TdT"]:
        for channels in channel_counts:
            for t in temperatures:
                sim = DNAKineticsSimulator(method=method, array_channels=channels, temp_c=t)
                res = sim.solve_economics(target_exabytes=1.0)
                
                # Market Gates
                # 1. Cost must be < $0.05 / GB to beat tape
                # 2. Time must be < 10 years to write 1 EB
                cost_pass = res['cost_per_gb_usd'] <= 0.05
                time_pass = res['years_to_write_1_EB'] <= 10.0
                
                status = "PASS" if (cost_pass and time_pass) else "FAIL (KILL)"
                if t == 50.0 and method == "Enzymatic_TdT":
                    status = "FAIL (ENZYME DENATURE)" # Thermal limit for TdT
                
                results.append({
                    "method": method,
                    "channels": channels,
                    "temp_c": t,
                    "time_per_cycle": res['eff_cycle_time_sec'],
                    "years_1EB": res['years_to_write_1_EB'],
                    "cost_gb": res['cost_per_gb_usd'],
                    "status": status
                })
                
                print(f"{method:<16} | {channels:<12.1e} | {t:<6.1f} | {res['eff_cycle_time_sec']:<10.2f} | {res['years_to_write_1_EB']:<12.1f} | ${res['cost_per_gb_usd']:<11.5f} | {status}")
                
    receipt = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "benchmark_engine": "v3.1.0-SOVEREIGN-EXACT-BOUNDED-KINETICS",
        "data": results
    }
    
    with open(RECEIPT_FILE, "w") as f:
        json.dump(receipt, f, indent=2)
    print("=================================================================")
    print(f"[RECEIPT] Written to {RECEIPT_FILE}")

if __name__ == "__main__":
    run_sensitivity_matrix()
