#!/usr/bin/env python3
"""
=============================================================================
XORAS RESEARCH & EMPIRICAL FALSIFICATION ENGINE:
CANDIDATE BBQ-003: MULTI-TIMESCALE LONG-DURATION ENERGY STORAGE (LDES)
=============================================================================
Pre-Registered Kill Specification v1.1.0 (SHA-256 Locked):
- Temporal Window: [50.0, 150.0] continuous discharge hours
- Lifespan: 1,000 deep cycles
- Numeric Kill Gates:
  1. Window Infimum Round-Trip Efficiency (RTE): >= 50.00%
  2. Capacity Fade per deep cycle ceiling: <= 0.020% / cycle
  3. Levelized Cost of Storage (LCOS) ceiling: <= $0.045 / kWh ($45.00 / MWh)
=============================================================================
Architectures Evaluated:
1. Iron-Air Battery (Form Energy archetype: alkaline Fe/air with HER side reactions)
2. Zinc-Air Flow Battery (Zn/air with dendrite & carbonate degradation)
3. Liquid Air Energy Storage (LAES: Claude-Linde cryo-liquefaction + thermal store)
4. Thermochemical Sponge Iron (Reversible steam-iron redox cycle)
5. Adversarial Baseline: Lithium Iron Phosphate (LFP) at 100+ hour duration
=============================================================================
"""

import os
import sys
import math
import json
import time
import hashlib
from datetime import datetime, timezone

SPEC_PATH = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/identity/pre_registered_kill_specifications.json"
EXPECTED_SPEC_SHA256 = "001c361e696b721e3442143288ab61c5711b3809c298dae797bd0b001ed36e52"

# Physical & Thermodynamic Constants
F_CONST = 96485.3321     # C/mol (Faraday constant)
R_GAS   = 8.314462618    # J/(mol K)
T_AMB   = 298.15         # K (25 C)

def load_and_verify_kill_spec() -> tuple:
    if not os.path.exists(SPEC_PATH):
        raise FileNotFoundError(f"Missing pre-registered spec: {SPEC_PATH}")
    with open(SPEC_PATH, "rb") as f:
        content = f.read()
    digest = hashlib.sha256(content).hexdigest()
    if digest != EXPECTED_SPEC_SHA256:
        raise ValueError(f"Specification tampering detected! Expected {EXPECTED_SPEC_SHA256}, got {digest}")
    data = json.loads(content.decode("utf-8"))
    return data["specifications"]["BBQ-003"], data.get("parent_spec_sha256", "UNKNOWN")

class LongDurationEnergyStorageSimulator:
    def __init__(self, architecture: str):
        self.arch = architecture

    def evaluate_architecture(self, t_discharge_hours: float, cycle_num: int = 1) -> dict:
        """
        Calculates exact Round-Trip Efficiency (RTE), Capacity Fade, and LCOS
        at a specific discharge duration and cycle number.
        """
        # Electricity input cost assumption: $0.025 / kWh ($25/MWh off-peak solar/wind)
        c_electricity_kwh = 0.025
        discount_rate = 0.07
        lifetime_years = 30.0

        if self.arch == "Iron-Air":
            # Electrochemical parameters:
            # E_rev = 1.28 V
            # V_discharge = 0.95 V (high air-cathode overpotential)
            # V_charge = 1.58 V (OER overpotential)
            eta_v = 0.95 / 1.58 # 60.13% voltage efficiency
            
            # Parasitic Hydrogen Evolution Reaction (HER) and chemical self-discharge:
            # Self-discharge rate: ~0.15% per day (0.00625% per hour)
            # Coulombic efficiency drops as discharge duration increases
            base_eta_c = 0.76 # Base Coulombic efficiency at 10h rate
            her_loss_rate_per_hour = 0.00065
            eta_c = max(0.40, base_eta_c - her_loss_rate_per_hour * t_discharge_hours)
            
            rte = eta_v * eta_c * 100.0
            
            # Degradation: Iron electrode passivation and air-breathing catalyst degradation
            # ~0.015% per deep cycle
            fade_per_cycle = 0.0145 # % per cycle
            capacity_retention = max(0.0, (1.0 - (fade_per_cycle / 100.0)) ** cycle_num)
            
            # Capital Costs:
            # Power block: $250 / kW
            # Energy storage (iron pellets + KOH): $18 / kWh
            capex_per_kw = 250.0 + 18.0 * t_discharge_hours
            capex_per_kwh = capex_per_kw / t_discharge_hours
            
            # Levelized Cost of Storage (LCOS):
            # LCOS = (CAPEX * CRF + Fixed_O&M) / (8760 * CF) + (c_elec / RTE)
            # For 100h battery: ~35 full cycles per year (CF ~ 0.40)
            annual_cycles = max(15.0, 4000.0 / t_discharge_hours)
            crf = (discount_rate * (1 + discount_rate)**lifetime_years) / ((1 + discount_rate)**lifetime_years - 1)
            capital_cost_per_kwh_delivered = (capex_per_kwh * crf + 1.50) / annual_cycles
            electricity_cost_per_kwh_delivered = c_electricity_kwh / (rte / 100.0)
            lcos = capital_cost_per_kwh_delivered + electricity_cost_per_kwh_delivered

            return {
                "architecture": self.arch,
                "t_discharge_hours": t_discharge_hours,
                "voltage_efficiency_percent": round(eta_v * 100.0, 2),
                "coulombic_efficiency_percent": round(eta_c * 100.0, 2),
                "round_trip_efficiency_percent": round(rte, 4),
                "capacity_fade_per_cycle_percent": round(fade_per_cycle, 4),
                "capacity_retention_at_1000_cycles": round(capacity_retention * 100.0, 2),
                "capex_per_kwh_installed": round(capex_per_kwh, 2),
                "lcos_usd_per_kwh": round(lcos, 5)
            }

        elif self.arch == "Zinc-Air-Flow":
            # V_discharge = 1.20 V, V_charge = 2.05 V
            eta_v = 1.20 / 2.05 # 58.54%
            # Coulombic efficiency higher than Fe-Air (less HER), but self-discharge exists
            base_eta_c = 0.90
            her_loss_per_hour = 0.00030
            eta_c = max(0.50, base_eta_c - her_loss_per_hour * t_discharge_hours)
            rte = eta_v * eta_c * 100.0
            
            # Severe degradation: Zinc dendrites, shape change, and alkaline carbonate poisoning
            fade_per_cycle = 0.0420 # % per cycle (Fails <= 0.020% ceiling)
            capacity_retention = max(0.0, (1.0 - (fade_per_cycle / 100.0)) ** cycle_num)
            
            capex_per_kw = 350.0 + 28.0 * t_discharge_hours
            capex_per_kwh = capex_per_kw / t_discharge_hours
            
            annual_cycles = max(15.0, 4000.0 / t_discharge_hours)
            crf = (discount_rate * (1 + discount_rate)**lifetime_years) / ((1 + discount_rate)**lifetime_years - 1)
            capital_cost_per_kwh_delivered = (capex_per_kwh * crf + 2.50) / annual_cycles
            electricity_cost_per_kwh_delivered = c_electricity_kwh / (rte / 100.0)
            lcos = capital_cost_per_kwh_delivered + electricity_cost_per_kwh_delivered

            return {
                "architecture": self.arch,
                "t_discharge_hours": t_discharge_hours,
                "voltage_efficiency_percent": round(eta_v * 100.0, 2),
                "coulombic_efficiency_percent": round(eta_c * 100.0, 2),
                "round_trip_efficiency_percent": round(rte, 4),
                "capacity_fade_per_cycle_percent": round(fade_per_cycle, 4),
                "capacity_retention_at_1000_cycles": round(capacity_retention * 100.0, 2),
                "capex_per_kwh_installed": round(capex_per_kwh, 2),
                "lcos_usd_per_kwh": round(lcos, 5)
            }

        elif self.arch == "Liquid-Air-LAES":
            # Cryogenic Liquefaction (Claude cycle) + High-Temperature Thermal Store (380 C)
            # Liquefaction exergy efficiency: 74%
            # Cold recovery + turbine expansion: 74%
            # High-grade thermal store integration yields steady RTE ~ 54.5%
            # Cryogenic tank boil-off loss is minimal: 0.04% per day (0.0016% per hour)
            boiloff_loss = 0.000016 * t_discharge_hours
            rte = (0.548 - boiloff_loss) * 100.0
            
            # Mechanical turbomachinery & cryo tanks: NO electrochemical dendrites/passivation!
            # Degradation over 1,000 cycles is minor mechanical wear: ~0.002% per cycle
            fade_per_cycle = 0.0020 # % per cycle (Passes <= 0.020% ceiling)
            capacity_retention = max(0.0, (1.0 - (fade_per_cycle / 100.0)) ** cycle_num)
            
            # Capital Cost:
            # Power block (cryo compressors, expanders, heat exchangers): $850 / kW
            # Thermal & Liquid Air Storage tanks: $6.50 / kWh
            capex_per_kw = 850.0 + 6.50 * t_discharge_hours
            capex_per_kwh = capex_per_kw / t_discharge_hours
            
            annual_cycles = max(15.0, 4000.0 / t_discharge_hours)
            crf = (discount_rate * (1 + discount_rate)**lifetime_years) / ((1 + discount_rate)**lifetime_years - 1)
            capital_cost_per_kwh_delivered = (capex_per_kwh * crf + 1.20) / annual_cycles
            electricity_cost_per_kwh_delivered = c_electricity_kwh / (rte / 100.0)
            lcos = capital_cost_per_kwh_delivered + electricity_cost_per_kwh_delivered

            return {
                "architecture": self.arch,
                "t_discharge_hours": t_discharge_hours,
                "voltage_efficiency_percent": 100.0, # Mechanical/thermodynamic cycle
                "coulombic_efficiency_percent": round((1.0 - boiloff_loss) * 100.0, 2),
                "round_trip_efficiency_percent": round(rte, 4),
                "capacity_fade_per_cycle_percent": round(fade_per_cycle, 4),
                "capacity_retention_at_1000_cycles": round(capacity_retention * 100.0, 2),
                "capex_per_kwh_installed": round(capex_per_kwh, 2),
                "lcos_usd_per_kwh": round(lcos, 5)
            }

        elif self.arch == "Thermochemical-Sponge-Iron":
            # Reversible Steam-Iron Redox (650 C)
            # High thermal efficiency when recuperated: RTE ~ 49.5% - 51.5%
            # Thermal radiation & pipe leakage:
            thermal_loss_per_hour = 0.00025 * t_discharge_hours
            rte = max(35.0, (0.518 - thermal_loss_per_hour) * 100.0)
            
            # Sintering of iron pellets over 1,000 cycles:
            fade_per_cycle = 0.0380 # % per cycle (Fails <= 0.020% ceiling)
            capacity_retention = max(0.0, (1.0 - (fade_per_cycle / 100.0)) ** cycle_num)
            
            capex_per_kw = 650.0 + 12.0 * t_discharge_hours
            capex_per_kwh = capex_per_kw / t_discharge_hours
            
            annual_cycles = max(15.0, 4000.0 / t_discharge_hours)
            crf = (discount_rate * (1 + discount_rate)**lifetime_years) / ((1 + discount_rate)**lifetime_years - 1)
            capital_cost_per_kwh_delivered = (capex_per_kwh * crf + 1.80) / annual_cycles
            electricity_cost_per_kwh_delivered = c_electricity_kwh / (rte / 100.0)
            lcos = capital_cost_per_kwh_delivered + electricity_cost_per_kwh_delivered

            return {
                "architecture": self.arch,
                "t_discharge_hours": t_discharge_hours,
                "voltage_efficiency_percent": 100.0,
                "coulombic_efficiency_percent": 98.0,
                "round_trip_efficiency_percent": round(rte, 4),
                "capacity_fade_per_cycle_percent": round(fade_per_cycle, 4),
                "capacity_retention_at_1000_cycles": round(capacity_retention * 100.0, 2),
                "capex_per_kwh_installed": round(capex_per_kwh, 2),
                "lcos_usd_per_kwh": round(lcos, 5)
            }

        else: # LFP Adversarial Baseline
            # Lithium Iron Phosphate
            rte = 88.50 # High efficiency
            fade_per_cycle = 0.0150 # Low fade
            capacity_retention = max(0.0, (1.0 - (fade_per_cycle / 100.0)) ** cycle_num)
            
            # Catastrophic cost scaling at 100h:
            # Cell + pack CAPEX = $110 / kWh (linear scaling!)
            capex_per_kw = 120.0 + 110.0 * t_discharge_hours
            capex_per_kwh = capex_per_kw / t_discharge_hours
            
            annual_cycles = max(15.0, 4000.0 / t_discharge_hours)
            crf = (discount_rate * (1 + discount_rate)**15.0) / ((1 + discount_rate)**15.0 - 1) # 15 yr life
            capital_cost_per_kwh_delivered = (capex_per_kwh * crf + 3.00) / annual_cycles
            electricity_cost_per_kwh_delivered = c_electricity_kwh / (rte / 100.0)
            lcos = capital_cost_per_kwh_delivered + electricity_cost_per_kwh_delivered

            return {
                "architecture": "LFP-Baseline",
                "t_discharge_hours": t_discharge_hours,
                "voltage_efficiency_percent": 93.0,
                "coulombic_efficiency_percent": 95.0,
                "round_trip_efficiency_percent": round(rte, 4),
                "capacity_fade_per_cycle_percent": round(fade_per_cycle, 4),
                "capacity_retention_at_1000_cycles": round(capacity_retention * 100.0, 2),
                "capex_per_kwh_installed": round(capex_per_kwh, 2),
                "lcos_usd_per_kwh": round(lcos, 5)
            }

def run_bbq003_continuous_window_benchmark() -> dict:
    spec, parent_sha = load_and_verify_kill_spec()
    thresholds = spec["numeric_kill_thresholds"]
    window_cfg = spec["temporal_window"]
    
    floor_rte = thresholds["window_infimum_round_trip_efficiency_percent"]
    ceil_fade = thresholds["capacity_fade_per_deep_cycle_ceiling_percent"]
    ceil_lcos = thresholds["levelized_cost_of_storage_ceiling_usd_per_kwh"]
    
    t_start = window_cfg["t_start_hours"]
    t_end = window_cfg["t_end_hours"]
    lifespan_cycles = window_cfg["cycle_lifespan_deep_cycles"]
    
    architectures = [
        "Iron-Air",
        "Zinc-Air-Flow",
        "Liquid-Air-LAES",
        "Thermochemical-Sponge-Iron",
        "LFP-Baseline"
    ]
    
    # Continuous Temporal Window Evaluation: sample 11 points in [50h, 150h]
    time_points = [t_start + i * (t_end - t_start) / 10.0 for i in range(11)]
    
    benchmark_results = {}
    
    for arch in architectures:
        sim = LongDurationEnergyStorageSimulator(arch)
        time_series = []
        for t_h in time_points:
            res = sim.evaluate_architecture(t_discharge_hours=t_h, cycle_num=lifespan_cycles)
            time_series.append(res)
            
        inf_rte = min(r["round_trip_efficiency_percent"] for r in time_series)
        sup_fade = max(r["capacity_fade_per_cycle_percent"] for r in time_series)
        sup_lcos = max(r["lcos_usd_per_kwh"] for r in time_series)
        at_100h_lcos = next(r["lcos_usd_per_kwh"] for r in time_series if abs(r["t_discharge_hours"] - 100.0) < 1e-3)
        
        gate_rte = inf_rte >= floor_rte
        gate_fade = sup_fade <= ceil_fade
        gate_lcos = at_100h_lcos <= ceil_lcos
        
        passed_all = gate_rte and gate_fade and gate_lcos
        verdict = "QUALIFIED" if passed_all else "KILLED"
        
        failure_reasons = []
        if not gate_rte:
            failure_reasons.append(f"RTE infimum {inf_rte:.2f}% < {floor_rte:.2f}%")
        if not gate_fade:
            failure_reasons.append(f"Capacity fade {sup_fade:.4f}%/cyc > {ceil_fade:.4f}%/cyc")
        if not gate_lcos:
            failure_reasons.append(f"100h LCOS ${at_100h_lcos:.4f}/kWh > ${ceil_lcos:.4f}/kWh")
            
        benchmark_results[arch] = {
            "verdict": verdict,
            "passed_all_gates": passed_all,
            "failure_reasons": failure_reasons,
            "window_infimum_rte_percent": round(inf_rte, 4),
            "window_supremum_fade_percent": round(sup_fade, 4),
            "nominal_100h_lcos_usd_per_kwh": round(at_100h_lcos, 5),
            "max_window_lcos_usd_per_kwh": round(sup_lcos, 5),
            "temporal_window_evaluations": time_series
        }
        
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "verified_kill_spec_sha256": EXPECTED_SPEC_SHA256,
        "temporal_window_hours": [t_start, t_end],
        "cycle_lifespan_evaluated": lifespan_cycles,
        "gates": {
            "infimum_rte_floor_percent": floor_rte,
            "capacity_fade_ceiling_percent": ceil_fade,
            "lcos_ceiling_usd_per_kwh": ceil_lcos
        },
        "results": benchmark_results
    }

if __name__ == "__main__":
    t0 = time.perf_counter()
    print("=================================================================")
    print("BBQ-003 CONTINUOUS TEMPORAL WINDOW EVALUATION ([50h, 150h])")
    print("=================================================================")
    
    bench = run_bbq003_continuous_window_benchmark()
    gates = bench["gates"]
    
    print(f"Gates: RTE >= {gates['infimum_rte_floor_percent']:.2f}% | Fade <= {gates['capacity_fade_ceiling_percent']:.4f}%/cyc | LCOS <= ${gates['lcos_ceiling_usd_per_kwh']:.3f}/kWh")
    print("-" * 88)
    print(f"{'Architecture':<24} {'Inf RTE (%)':<13} {'Fade (%/cyc)':<14} {'100h LCOS ($/kWh)':<18} {'Verdict'}")
    print("-" * 88)
    
    for arch, d in bench["results"].items():
        v = d["verdict"]
        print(f"{arch:<24} {d['window_infimum_rte_percent']:<13.2f} {d['window_supremum_fade_percent']:<14.4f} ${d['nominal_100h_lcos_usd_per_kwh']:<17.4f} {v}")
        if d["failure_reasons"]:
            print(f"  └─ Kill Triggers: {', '.join(d['failure_reasons'])}")
            
    out_path = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/docs/audits/BBQ_003_EMPIRICAL_QUALIFICATION_RECEIPT.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(bench, f, indent=2)
        
    print("-----------------------------------------------------------------")
    print(f"[+] Receipt Certified & Saved: {out_path}")
    print(f"[+] Benchmark Execution Duration: {time.perf_counter() - t0:.3f}s")
    print("=================================================================")
