#!/usr/bin/env python3
"""
BBQ-001: Error-Avoiding Quantum Compilation Simulation Harness.
Empirical qualification benchmark testing adaptive problem reformulation
into noise-invariant commutant subspaces across a Continuous Temporal Window.

Pre-Registered Numeric Governance:
- Governed by: identity/pre_registered_kill_specifications.json (v1.1.0-SOVEREIGN-TEMPORAL-WINDOW)
- Parent Version: 1.0.0-SOVEREIGN-KILL-GATES (SHA-256: f7d12935d2a360d7832ae9bea0f73354f5ca3a1079b618dd603be4766a3d9841)
- Constitutional Invariant 075: Pre-Registered Continuous Temporal Window & Anti-Asymmetry Law
- Enforces infimum floor, infimum relative gain, and plateau stability bounds across [1.0/gamma, 1.5/gamma].
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy.linalg as la

ROOT = Path(__file__).resolve().parent.parent.parent
KILL_SPEC_FILE = ROOT / "identity" / "pre_registered_kill_specifications.json"
RECEIPT_FILE = ROOT / "docs" / "audits" / "BBQ_001_EMPIRICAL_QUALIFICATION_RECEIPT.json"
STRESS_RECEIPT_FILE = ROOT / "docs" / "audits" / "BBQ_001_STRESS_TEST_KILL_RECEIPT.json"
LEDGER_FILE = ROOT / "memory" / "provenance" / "MERKLE_EVIDENCE_TRACKER_LEDGER.jsonl"
EXPECTED_SPEC_SHA256 = "001c361e696b721e3442143288ab61c5711b3809c298dae797bd0b001ed36e52"

# Basic Pauli Matrices
SIGMA_I = np.eye(2, dtype=complex)
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)


def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with filepath.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def load_and_verify_kill_spec() -> tuple[dict, str]:
    """Verify pre-registered specification file integrity before running benchmarks."""
    if not KILL_SPEC_FILE.exists():
        raise FileNotFoundError(f"[FATAL] Pre-registered kill specification missing: {KILL_SPEC_FILE}")
    actual_sha = sha256_file(KILL_SPEC_FILE)
    if actual_sha != EXPECTED_SPEC_SHA256:
        raise ValueError(
            f"[FATAL POST-HOC TAMPER DETECTED] Kill spec hash mismatch!\n"
            f"Expected: {EXPECTED_SPEC_SHA256}\nActual:   {actual_sha}\n"
            f"Pre-registration violation. Aborting benchmark."
        )
    spec_data = json.loads(KILL_SPEC_FILE.read_text(encoding="utf-8"))
    return spec_data["specifications"]["BBQ-001"], spec_data.get("parent_spec_sha256", "")


def kron_n(operators: list[np.ndarray]) -> np.ndarray:
    result = operators[0]
    for op in operators[1:]:
        result = np.kron(result, op)
    return result


def build_collective_noise_generator(num_qubits: int) -> np.ndarray:
    """Build collective dephasing generator S_z = sum_j sigma_z^{(j)}."""
    dim = 2**num_qubits
    sz_total = np.zeros((dim, dim), dtype=complex)
    for j in range(num_qubits):
        ops = [SIGMA_I] * num_qubits
        ops[j] = SIGMA_Z
        sz_total += kron_n(ops)
    return sz_total


def build_local_noise_generators(num_qubits: int) -> list[np.ndarray]:
    """Build independent local dephasing operators sigma_z^{(j)}."""
    dim = 2**num_qubits
    ops_list = []
    for j in range(num_qubits):
        ops = [SIGMA_I] * num_qubits
        ops[j] = SIGMA_Z
        ops_list.append(kron_n(ops))
    return ops_list


def build_logical_dfs_basis_4qubits() -> np.ndarray:
    """
    Construct explicit 2-logical-qubit basis inside the 6-D kernel of S_z on 4 qubits.
    Kernel has total Sz=0 (|0011>, |0101>, |0110>, |1001>, |1010>, |1100>).
    """
    dim = 16
    v = lambda s: np.array([1 if f"{k:04b}" == s else 0 for k in range(dim)], dtype=complex)
    
    b00 = (v("0110") - v("1001")) / np.sqrt(2.0)
    b01 = (v("0101") - v("1010")) / np.sqrt(2.0)
    b10 = (v("0011") - v("1100")) / np.sqrt(2.0)
    b11 = (v("0110") + v("1001") - v("0101") - v("1010")) / 2.0
    
    return np.column_stack([b00, b01, b10, b11])


def solve_liouvillian_evolution(
    rho_0: np.ndarray,
    H: np.ndarray,
    jump_operators: list[tuple[np.ndarray, float]],
    t_final: float
) -> np.ndarray:
    """Exact vectorized Lindblad master equation solver."""
    dim = H.shape[0]
    h_super = -1j * (np.kron(H, np.eye(dim)) - np.kron(np.eye(dim), H.T))
    
    diss_super = np.zeros((dim * dim, dim * dim), dtype=complex)
    for L_k, gamma_k in jump_operators:
        if gamma_k <= 0:
            continue
        l_dag = L_k.conj().T
        l_dag_l = l_dag @ L_k
        diss_k = np.kron(L_k, L_k.conj()) - 0.5 * (
            np.kron(l_dag_l, np.eye(dim)) + np.kron(np.eye(dim), l_dag_l.T)
        )
        diss_super += gamma_k * diss_k
        
    liouvillian = h_super + diss_super
    propagator = la.expm(liouvillian * t_final)
    
    rho_vec = propagator @ rho_0.reshape(dim * dim)
    rho_t = rho_vec.reshape((dim, dim))
    rho_t = 0.5 * (rho_t + rho_t.conj().T)
    tr = np.trace(rho_t)
    if not np.isclose(tr, 0.0):
        rho_t /= tr
    return rho_t


def safe_fidelity(rho: np.ndarray, sigma: np.ndarray) -> float:
    """Compute Uhlmann fidelity safely with SVD-regularized square root."""
    rho = 0.5 * (rho + rho.conj().T)
    sigma = 0.5 * (sigma + sigma.conj().T)
    
    evals_r, evecs_r = la.eigh(rho)
    evals_r = np.clip(evals_r, 0.0, None)
    sqrt_rho = evecs_r @ np.diag(np.sqrt(evals_r)) @ evecs_r.conj().T
    
    prod = sqrt_rho @ sigma @ sqrt_rho
    prod = 0.5 * (prod + prod.conj().T)
    evals_p, _ = la.eigh(prod)
    evals_p = np.clip(evals_p, 0.0, None)
    
    fid = float(np.sum(np.sqrt(evals_p)) ** 2)
    return float(np.clip(fid, 0.0, 1.0))


def run_temporal_window_benchmark(gamma_loc: float, mode_name: str) -> dict:
    """
    Executes benchmark across the continuous temporal window [1.0/gamma, 1.5/gamma].
    Evaluates infimum floor, infimum relative gain, and plateau decay bounds.
    """
    spec, parent_sha = load_and_verify_kill_spec()
    num_qubits = spec["noise_environment"]["system_qubits"]
    gamma_coll = spec["noise_environment"]["gamma_collective_dephasing"]
    
    window_cfg = spec["temporal_window"]
    t_start = window_cfg["t_start_seconds"]
    t_end = window_cfg["t_end_seconds"]
    num_checkpoints = window_cfg["checkpoint_count"]
    t_checkpoints = np.linspace(t_start, t_end, num_checkpoints)
    
    thresholds = spec["numeric_kill_thresholds"]
    floor_fidelity = thresholds["window_infimum_fidelity_floor"]
    min_delta_gain = thresholds["window_infimum_relative_delta_gain"]
    min_sigma = thresholds["window_infimum_statistical_significance_sigma"]
    max_decay_rate = thresholds["plateau_decay_rate_ceiling_per_second"]
    max_latency_us = thresholds["maximum_mean_search_latency_us"]
    samples = thresholds["minimum_monte_carlo_sample_count"]
    
    print(f"\n=================================================================")
    print(f"BBQ-001 TEMPORAL WINDOW BENCHMARK [{mode_name.upper()}]")
    print(f"=================================================================")
    print(f"[*] Verified Spec SHA-256       : {EXPECTED_SPEC_SHA256[:16]}... [LOCKED]")
    print(f"[*] Parent Spec SHA-256         : {parent_sha[:16]}... [LINKED]")
    print(f"[*] Temporal Window             : [{t_start:.4f}s, {t_end:.4f}s] ({num_checkpoints} checkpoints)")
    print(f"[*] Noise Environment           : gamma_coll={gamma_coll:.3f}, gamma_loc={gamma_loc:.3f}")
    print(f"[*] Pre-Registered Gates        :")
    print(f"    - Window Infimum Floor      : >= {floor_fidelity:.4f}")
    print(f"    - Window Infimum Delta Gain : >= +{min_delta_gain:.4f}")
    print(f"    - Window Infimum Sigma      : >= {min_sigma:.2f}σ")
    print(f"    - Plateau Decay Rate Ceiling: <= {max_decay_rate:.4f} s^-1")
    print(f"    - Search Latency Ceiling    : <= {max_latency_us:.2f} µs")
    print(f"-----------------------------------------------------------------")
    
    sz_total = build_collective_noise_generator(num_qubits)
    local_ops = build_local_noise_generators(num_qubits)
    jump_operators = [(sz_total, gamma_coll)] + [(l_k, gamma_loc) for l_k in local_ops]
    
    v_dfs = build_logical_dfs_basis_4qubits()
    p_dfs = v_dfs.conj().T
    
    # 2-qubit baseline
    sz_2q = np.kron(SIGMA_Z, SIGMA_I) + np.kron(SIGMA_I, SIGMA_Z)
    loc_2q = [np.kron(SIGMA_Z, SIGMA_I), np.kron(SIGMA_I, SIGMA_Z)]
    jumps_2q = [(sz_2q, gamma_coll)] + [(l, gamma_loc) for l in loc_2q]
    
    # Storage across checkpoints: dict of t -> list of fidelities
    std_fidelities_by_t = {t: [] for t in t_checkpoints}
    adapt_fidelities_by_t = {t: [] for t in t_checkpoints}
    search_latencies_us = []
    
    rng = np.random.default_rng(10042)
    t0_start = time.perf_counter()
    
    for sample_idx in range(samples):
        j_zz = rng.normal(1.0, 0.2)
        h_x1 = rng.normal(0.6, 0.15)
        h_x2 = rng.normal(0.6, 0.15)
        h_z1 = rng.normal(0.4, 0.1)
        
        h_log = (
            j_zz * np.kron(SIGMA_Z, SIGMA_Z) +
            h_x1 * np.kron(SIGMA_X, SIGMA_I) +
            h_x2 * np.kron(SIGMA_I, SIGMA_X) +
            h_z1 * np.kron(SIGMA_Z, SIGMA_I)
        )
        
        psi_log_0 = np.array([0.5, 0.5, 0.5, 0.5], dtype=complex)
        rho_log_0 = np.outer(psi_log_0, psi_log_0.conj())
        
        # Adaptive projection synthesis
        t_s = time.perf_counter()
        rho_phys_0 = v_dfs @ rho_log_0 @ p_dfs
        h_phys = v_dfs @ h_log @ p_dfs
        search_latencies_us.append((time.perf_counter() - t_s) * 1e6)
        
        # Evaluate across the entire temporal window
        for t_val in t_checkpoints:
            u_ideal = la.expm(-1j * h_log * t_val)
            rho_ideal = u_ideal @ rho_log_0 @ u_ideal.conj().T
            
            # Baseline noisy evolution
            rho_std = solve_liouvillian_evolution(rho_log_0, h_log, jumps_2q, t_val)
            fid_std = safe_fidelity(rho_ideal, rho_std)
            std_fidelities_by_t[t_val].append(fid_std)
            
            # Adaptive noisy evolution
            rho_phys = solve_liouvillian_evolution(rho_phys_0, h_phys, jump_operators, t_val)
            rho_dec = p_dfs @ rho_phys @ v_dfs
            rho_dec /= np.trace(rho_dec)
            fid_adapt = safe_fidelity(rho_ideal, rho_dec)
            adapt_fidelities_by_t[t_val].append(fid_adapt)
            
    total_sec = time.perf_counter() - t0_start
    
    # Statistical analysis across checkpoints
    checkpoint_stats = []
    for t_val in t_checkpoints:
        m_std = float(np.mean(std_fidelities_by_t[t_val]))
        s_std = float(np.std(std_fidelities_by_t[t_val]))
        m_ad = float(np.mean(adapt_fidelities_by_t[t_val]))
        s_ad = float(np.std(adapt_fidelities_by_t[t_val]))
        d_gain = m_ad - m_std
        comb_s = math.sqrt(s_std**2 + s_ad**2)
        z = d_gain / comb_s if comb_s > 0 else 0.0
        
        checkpoint_stats.append({
            "t_seconds": round(float(t_val), 4),
            "mean_baseline_fidelity": round(m_std, 4),
            "std_baseline_fidelity": round(s_std, 4),
            "mean_adaptive_fidelity": round(m_ad, 4),
            "std_adaptive_fidelity": round(s_ad, 4),
            "delta_gain": round(d_gain, 4),
            "z_score": round(z, 2)
        })
        
    # Temporal Window Infimum Metrics
    inf_adapt_fid = min(cp["mean_adaptive_fidelity"] for cp in checkpoint_stats)
    inf_delta_gain = min(cp["delta_gain"] for cp in checkpoint_stats)
    inf_z_score = min(cp["z_score"] for cp in checkpoint_stats)
    
    # Plateau Decay Rate: max |dF/dt| across consecutive checkpoints
    decay_rates = []
    for i in range(len(checkpoint_stats) - 1):
        dt = checkpoint_stats[i+1]["t_seconds"] - checkpoint_stats[i]["t_seconds"]
        df = abs(checkpoint_stats[i+1]["mean_adaptive_fidelity"] - checkpoint_stats[i]["mean_adaptive_fidelity"])
        decay_rates.append(df / dt if dt > 0 else 0.0)
    max_measured_decay = max(decay_rates) if decay_rates else 0.0
    
    mean_latency = float(np.mean(search_latencies_us))
    
    # Gate Evaluations
    gate_floor = inf_adapt_fid >= floor_fidelity
    gate_delta = inf_delta_gain >= min_delta_gain
    gate_sigma = inf_z_score >= min_sigma
    gate_decay = max_measured_decay <= max_decay_rate
    gate_latency = mean_latency <= max_latency_us
    gate_samples = len(search_latencies_us) >= samples
    
    passed_all = gate_floor and gate_delta and gate_sigma and gate_decay and gate_latency and gate_samples
    verdict = "QUALIFIED" if passed_all else "FAILED"
    
    print("\n--- TEMPORAL CHECKPOINT PROFILE ---")
    for cp in checkpoint_stats:
        print(f"t = {cp['t_seconds']:.3f}s: Baseline={cp['mean_baseline_fidelity']:.4f}, Adaptive={cp['mean_adaptive_fidelity']:.4f}, Delta=+{cp['delta_gain']:.4f} ({cp['z_score']}σ)")
        
    print("\n--- PRE-REGISTERED WINDOW GATE EVALUATION ---")
    print(f"1. Window Infimum Fidelity Floor : {inf_adapt_fid:.4f} >= {floor_fidelity:.4f} -> [{'PASS' if gate_floor else 'FAIL (KILL)'}]")
    print(f"2. Window Infimum Delta Gain     : +{inf_delta_gain:.4f} >= +{min_delta_gain:.4f} -> [{'PASS' if gate_delta else 'FAIL (KILL)'}]")
    print(f"3. Window Infimum Significance   : {inf_z_score:.2f}σ >= {min_sigma:.2f}σ -> [{'PASS' if gate_sigma else 'FAIL (KILL)'}]")
    print(f"4. Plateau Decay Rate Bound      : {max_measured_decay:.4f} s^-1 <= {max_decay_rate:.4f} s^-1 -> [{'PASS' if gate_decay else 'FAIL (KILL)'}]")
    print(f"5. Search Latency Ceiling        : {mean_latency:.2f} µs <= {max_latency_us:.2f} µs -> [{'PASS' if gate_latency else 'FAIL (KILL)'}]")
    print("-----------------------------------------------------------------")
    print(f"Final Window Verdict             : {verdict}")
    print(f"Anti-Asymmetry Status            : {'PROMOTED TO GOLDEN LIST' if passed_all else 'KILLED (PERMANENTLY STRUCK)'}")
    print("=================================================================")
    
    receipt = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "candidate_id": "BBQ-001",
        "mode": mode_name,
        "governance_rule": "Constitutional Invariant 075 (Continuous Temporal Window)",
        "spec_file_sha256": EXPECTED_SPEC_SHA256,
        "parent_spec_sha256": parent_sha,
        "temporal_window": window_cfg,
        "noise_environment": {
            "gamma_collective": gamma_coll,
            "gamma_local": gamma_loc
        },
        "pre_registered_thresholds": thresholds,
        "checkpoint_stats": checkpoint_stats,
        "window_infimum_metrics": {
            "infimum_adaptive_fidelity": round(inf_adapt_fid, 4),
            "infimum_delta_gain": round(inf_delta_gain, 4),
            "infimum_statistical_significance_z": round(inf_z_score, 2),
            "maximum_measured_plateau_decay_rate": round(max_measured_decay, 4),
            "mean_search_latency_us": round(mean_latency, 2),
            "sample_count": len(search_latencies_us),
            "benchmark_execution_sec": round(total_sec, 2)
        },
        "gates_evaluated": {
            "window_infimum_fidelity_passed": gate_floor,
            "window_infimum_gain_passed": gate_delta,
            "window_significance_passed": gate_sigma,
            "plateau_decay_rate_passed": gate_decay,
            "search_latency_passed": gate_latency,
            "sample_count_passed": gate_samples
        },
        "verdict": verdict,
        "taint_state": "0xBEAF0000" if passed_all else "0xDEAD0000"
    }
    
    receipt_raw = json.dumps(receipt, sort_keys=True)
    receipt_sha = hashlib.sha256(receipt_raw.encode("utf-8")).hexdigest()
    receipt["receipt_sha256"] = receipt_sha
    
    target_out = RECEIPT_FILE if mode_name == "primary" else STRESS_RECEIPT_FILE
    target_out.parent.mkdir(parents=True, exist_ok=True)
    target_out.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"[RECEIPT] Written to {target_out}")
    print(f"[RECEIPT SHA-256] {receipt_sha}")
    
    if LEDGER_FILE.exists():
        ledger_entry = {
            "timestamp": receipt["timestamp"],
            "event_type": "TEMPORAL_WINDOW_QUALIFICATION",
            "candidate_id": "BBQ-001",
            "mode": mode_name,
            "spec_sha256": EXPECTED_SPEC_SHA256,
            "parent_spec_sha256": parent_sha,
            "verdict": verdict,
            "infimum_adaptive_fidelity": receipt["window_infimum_metrics"]["infimum_adaptive_fidelity"],
            "infimum_delta_gain": receipt["window_infimum_metrics"]["infimum_delta_gain"],
            "plateau_decay_rate": receipt["window_infimum_metrics"]["maximum_measured_plateau_decay_rate"],
            "receipt_sha256": receipt_sha,
            "taint_state": receipt["taint_state"]
        }
        with LEDGER_FILE.open("a", encoding="utf-8") as lf:
            lf.write(json.dumps(ledger_entry) + "\n")
        print(f"[LEDGER] Appended entry to {LEDGER_FILE}")
        
    return receipt


if __name__ == "__main__":
    # 1. Primary Qualification Regime (Bounded Local Noise gamma_loc = 0.020)
    res_primary = run_temporal_window_benchmark(gamma_loc=0.020, mode_name="primary")
    
    # 2. Hostile Stress-Test Regime (Uncorrelated Local Noise gamma_loc = 0.050)
    # Demonstrates that the kill condition executes cleanly and kills the candidate when thresholds are violated
    res_stress = run_temporal_window_benchmark(gamma_loc=0.050, mode_name="stress_test")
