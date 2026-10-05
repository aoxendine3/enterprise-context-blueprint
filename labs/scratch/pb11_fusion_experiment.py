import numpy as np
import json

print("Initializing p-B11 Aneutronic Fusion Plasma Simulation...")
# T in keV. 1 keV = 11.6 million Kelvin
temperatures = np.linspace(300, 800, 100)
results = []

for T in temperatures:
    # Bremsstrahlung loss scaling
    P_brems = 4.0 * (T**0.5) 
    # Reactivity peak at 600 keV for p-B11
    reactivity = np.exp(-((T-600)**2)/40000)
    P_fusion = 120.0 * reactivity
    
    net_power = P_fusion - P_brems
    status = "IGNITION_SURVIVAL" if net_power > 0 else "RADIATIVE_COLLAPSE"
    
    results.append({
        "temp_keV": round(T, 1),
        "P_brems_MW": round(P_brems, 2),
        "P_fusion_MW": round(P_fusion, 2),
        "net_power_MW": round(net_power, 2),
        "status": status
    })

survival_points = [r for r in results if r["status"] == "IGNITION_SURVIVAL"]
if survival_points:
    boundary = survival_points[0]
else:
    boundary = {"temp_keV": "NONE", "status": "FAIL"}

out = {
    "target": "p-B11 Aneutronic Fusion",
    "physics_verdict": "KILLED AT STANDARD TEMPERATURES" if not survival_points else "QUALIFIED AT SPECIFIC THERMAL BOUNDARY",
    "survival_boundary_start": boundary,
    "survival_boundary_end": survival_points[-1] if survival_points else None
}

with open("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/scratch/pb11_fusion_results.json", "w") as f:
    json.dump(out, f, indent=2)

print(f"Simulation Complete. Survival Boundary Start: {boundary['temp_keV']} keV")
