import numpy as np
from scipy.integrate import solve_ivp

# Simulating Landau-Zener transition with environmental coupling (Anti-KZM)
delta = 1.0
gamma = 0.05 # Bandwidth cap / Environmental dissipation

def lindblad(t, rho_vec, v):
    r00, r01, r10, r11 = rho_vec
    hz = 0.5 * v * t
    hx = 0.5 * delta
    
    dr00 = -1j * hx * (r10 - r01)
    dr11 = -1j * hx * (r01 - r10)
    dr01 = -1j * (2*hz*r01 + hx*(r11 - r00))
    dr10 = -1j * (-2*hz*r10 + hx*(r00 - r11))
    
    # Dissipation modeling finite-T / bandwidth cap
    dr00 += gamma * (r11 - r00)
    dr11 += gamma * (r00 - r11)
    dr01 -= gamma * r01
    dr10 -= gamma * r10
    
    return [dr00, dr01, dr10, dr11]

quench_times = [1.0, 5.0, 15.0, 30.0, 60.0, 100.0]
results = []

for tau_q in quench_times:
    v = 1.0 / tau_q
    t_span = (-10*tau_q, 10*tau_q)
    rho0 = [1+0j, 0j, 0j, 0j]
    sol = solve_ivp(lindblad, t_span, rho0, args=(v,), t_eval=[t_span[1]], method='RK45')
    defect_density = np.real(sol.y[0][-1])
    results.append((tau_q, defect_density))

print("=== SOVEREIGN KZM BARE-METAL SIMULATION ===")
print("Quench_Time(tau) | Defect_Density")
for tau, d in results:
    print(f"{tau:16.1f} | {d:.4f}")
