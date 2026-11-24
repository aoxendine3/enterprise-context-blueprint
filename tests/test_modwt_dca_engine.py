#!/usr/bin/env python3
"""Empirical + negative tests for the MODWT-DCA innate-immunity engine.

Negative cases are the point: fail-closed inputs must never return SAFE,
invalid thresholds must raise, and the pipeline must fire on a real danger
burst inside the mDC range sovereign_runtime.py actually produces.
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "core/governance"))
from modwt_dca_engine import (
    analyze, compute_mcav, extract_signal, from_runtime, modwt_details,
    DEFAULT_THRESHOLD, MIN_SAMPLES,
)
from sovereign_runtime import SovereignRuntime

R = {}


def check(name, cond):
    print(f"[{'PASS' if cond else 'FAIL'}] {name}")
    return bool(cond)


# --- 1. MODWT transform oracle (hand-computed, independent of engine) ---
sig4 = [1.0, 2.0, 3.0, 4.0]
d1 = modwt_details(sig4, levels=1)[0]
# out[i] = (x[i-1] - x[i]) / sqrt(2), circular: [3/rt2, -1/rt2, -1/rt2, -1/rt2]
expected = [3.0 / math.sqrt(2.0), -1.0 / math.sqrt(2.0),
            -1.0 / math.sqrt(2.0), -1.0 / math.sqrt(2.0)]
R["modwt_oracle"] = check(
    "MODWT scale-1 matches hand-computed Haar oracle",
    all(abs(a - b) < 1e-9 for a, b in zip(d1, expected)))

# --- 2. Constant signal: no structure => MCAV 0, BASAL ---
rep = analyze(signal=[2.0] * 32)
R["constant_basal"] = check(
    "constant signal -> MCAV 0, status OK, verdict BASAL",
    rep["status"] == "OK" and rep["mcav"] == 0.0 and rep["verdict"] == "BASAL")

# --- 3. Slow sine: smooth baseline stays BASAL ---
sine = [math.sin(2.0 * math.pi * i / 16.0) for i in range(64)]
rep = analyze(signal=sine)
R["sine_basal"] = check(
    "smooth periodic signal -> BASAL",
    rep["status"] == "OK" and rep["verdict"] == "BASAL")

# --- 4. Transient spike on a quiet baseline -> DANGER at the spike index ---
n = 64
baseline = [i * 0.001 for i in range(n)]
spike_idx = 40
spiky = list(baseline)
spiky[spike_idx] = 1.0
rep = analyze(signal=spiky)
details = modwt_details(spiky, levels=rep["levels"])
argmax = max(range(n), key=lambda i: abs(details[0][i]))
R["spike_danger"] = check(
    "transient spike -> verdict DANGER",
    rep["status"] == "OK" and rep["verdict"] == "DANGER")
R["spike_localized"] = check(
    "finest-scale peak localizes to the injected spike index",
    argmax in (spike_idx - 1, spike_idx, spike_idx + 1))

# --- 5. NEGATIVE: fail-closed inputs must never return SAFE ---
rep = analyze(signal=[])
R["empty_fail_closed"] = check(
    "empty signal -> FAIL_CLOSED (not SAFE)",
    rep["status"] == "FAIL_CLOSED" and rep["verdict"] == "FAIL_CLOSED"
    and rep["reason"] == "EMPTY_SIGNAL")

rep = analyze(signal=[1.0] * (MIN_SAMPLES - 1))
R["short_fail_closed"] = check(
    f"signal shorter than {MIN_SAMPLES} -> FAIL_CLOSED INSUFFICIENT_SAMPLES",
    rep["status"] == "FAIL_CLOSED" and rep["reason"] == "INSUFFICIENT_SAMPLES")

bad = [0.1] * 32
bad[7] = float("nan")
rep = analyze(signal=bad)
R["nan_fail_closed"] = check("NaN sample -> FAIL_CLOSED NON_FINITE_SIGNAL",
                             rep["status"] == "FAIL_CLOSED"
                             and rep["reason"] == "NON_FINITE_SIGNAL")

bad = [0.1] * 32
bad[3] = float("inf")
rep = analyze(signal=bad)
R["inf_fail_closed"] = check("inf sample -> FAIL_CLOSED",
                             rep["status"] == "FAIL_CLOSED")

rep = analyze(signal=None, antigens=None)
R["no_input_fail_closed"] = check("no input at all -> FAIL_CLOSED NO_INPUT",
                                  rep["reason"] == "NO_INPUT")

rep = analyze(signal=[1.0] * 32, antigens=[{"mDC": 1.0}] * 32)
R["ambiguous_fail_closed"] = check("both inputs -> FAIL_CLOSED AMBIGUOUS_INPUT",
                                   rep["reason"] == "AMBIGUOUS_INPUT")

rep = analyze(antigens=[{"kind": "x"}] * 32)
R["malformed_fail_closed"] = check("record without mDC/pamp/ds -> FAIL_CLOSED",
                                   rep["status"] == "FAIL_CLOSED"
                                   and "MALFORMED_INPUT" in rep["reason"])

rep = analyze(antigens=[{"mDC": "bad"}] * 32)
R["string_mcav_fail_closed"] = check("non-numeric mDC -> FAIL_CLOSED",
                                     rep["status"] == "FAIL_CLOSED")

rep = analyze(antigens=[{"mDC": 1.0}] * 31 + [{"mDC": float("nan")}])
R["nan_antigen_fail_closed"] = check("NaN mDC record -> FAIL_CLOSED",
                                     rep["status"] == "FAIL_CLOSED")

# --- 6. NEGATIVE: invalid threshold / levels raise (never silently pass) ---
raised = 0
for thr in (0, -1.0, float("nan"), float("inf"), "1.0", None):
    try:
        analyze(signal=[1.0] * 32, threshold=thr)
    except ValueError:
        raised += 1
R["threshold_validation"] = check(
    f"invalid thresholds raise ValueError ({raised}/6)",
    raised == 6)

raised = 0
for lv in (0, -2, 1.5, "4", True):
    try:
        analyze(signal=[1.0] * 32, levels=lv)
    except ValueError:
        raised += 1
R["levels_validation"] = check(f"invalid levels raise ValueError ({raised}/5)",
                               raised == 5)

# --- 7. extract_signal recomputes mDC when the record lacks it ---
sig = extract_signal([{"pamp": 1.0, "ds": 0.3, "ss": 1.0}])
R["mcv_formula"] = check(
    "fallback mDC = 2*pamp + ds - 1.5*ss matches sovereign_runtime",
    abs(sig[0] - (2.0 * 1.0 + 0.3 - 1.5 * 1.0)) < 1e-12)

# --- 8. Integration with the live SovereignRuntime antigen stream ---
rt = SovereignRuntime()
# Benign history: clustered stale-plan antigens with micro-jitter (mDC ~ -0.9).
for k in range(31):
    rt._record_antigen("STALE_PLAN", pamp=0.0, ds=0.6 + 0.004 * (k % 3))
rep = from_runtime(rt)
R["runtime_benign_basal"] = check(
    "live runtime, benign antigen history -> BASAL",
    rep["status"] == "OK" and rep["verdict"] == "BASAL")
# Danger burst: ledger-verify failures (mDC = 0.8) arrive on top of it.
for _ in range(3):
    rt._record_antigen("CAP_LEDGER_FAIL", pamp=1.0, ds=0.3)
rep = from_runtime(rt)
R["runtime_burst_danger"] = check(
    "live runtime, danger burst (mDC jump -0.9 -> 0.8) -> DANGER",
    rep["status"] == "OK" and rep["verdict"] == "DANGER")

# --- 9. Threshold semantics: raising the threshold suppresses the same burst ---
rep_low = from_runtime(rt, threshold=DEFAULT_THRESHOLD)
rep_high = from_runtime(rt, threshold=1e9)
R["threshold_suppresses"] = check(
    "raising threshold above MCAV flips DANGER -> BASAL",
    rep_low["verdict"] == "DANGER" and rep_high["verdict"] == "BASAL")

# --- 10. Degrade path: too few runtime antigens -> FAIL_CLOSED ---
tiny = SovereignRuntime()
tiny._record_antigen("STALE_PLAN", pamp=0.0, ds=0.6)
rep = from_runtime(tiny)
R["runtime_short_fail_closed"] = check(
    "runtime with 1 antigen -> FAIL_CLOSED (not SAFE)",
    rep["status"] == "FAIL_CLOSED")

print("-" * 60)
allpass = all(R.values())
print(f"checks: {len(R)} | failed: {sum(1 for v in R.values() if not v)}")
print("VERDICT:", "MODWT_DCA_PASS" if allpass else "MODWT_DCA_FAIL")
raise SystemExit(0 if allpass else 1)
