#!/usr/bin/env python3
"""
MODWT-DCA ENGINE — Innate Immunity (Bio-Cognitive Core, chapter 4 pipeline).

Implements the exact three-stage pipeline specified in the XORAS Bio-Cognitive
Core video ("Innate Immunity — MODWT-DCA Engine"):

  1. INGEST  — Ingest PAMP, Danger, and Safe Signals.
               Reads SovereignRuntime.antigens records produced by
               sovereign_runtime.py (mDC = 2*pamp + ds - 1.5*ss already
               computed there; record key "mDC").
  2. FILTER  — Apply MODWT Wavelet Decomposition.
               Maximal Overlap Discrete Wavelet Transform via the a-trous
               (stationary) algorithm: Haar filter pair, circular boundary
               handling, J dyadic scales (dilated filters with 2^(j-1)-1
               zeros between taps).
  3. MCAV    — Compute Mature Context Antigen Value, compared against a
               Threshold.

MCAV definition (honest, documented): the most anomalous scale of the MODWT
decomposition — for each scale j, the peak detail coefficient is normalized by
that scale's own robust background spread (MAD/0.6745) and the universal
threshold factor sqrt(2*ln(N)) (Donoho-Johnstone); MCAV is the maximum ratio
across scales. Per-scale normalization means slow physiological drift
(coarse-scale energy) is not mistaken for an antigen transient, while a spike
(dominant at fine scales against a quiet background) is. MCAV > threshold
(default 1.0) => DANGER, otherwise BASAL. A constant/degenerate signal has no
structure => MCAV 0.

Fail-closed law: empty, too-short, or non-finite signals return a report with
status FAIL_CLOSED — never SAFE. threshold must be a positive finite number
and levels a positive integer (ValueError). No numpy: stdlib only, matching
the core/governance style (mbc_layer.py, sovereign_runtime.py).

STATUS: production module with empirical + negative tests in
tests/test_modwt_dca_engine.py; wired to the evidence DAG via test_pass.
"""
from __future__ import annotations

import math
import statistics
from typing import Any, Dict, List, Optional, Sequence

# Haar MODWT filter pair (unit norm). Sign convention of the high-pass is
# irrelevant: MCAV uses |coefficients|.
_HAAR_LO = (1.0 / math.sqrt(2.0), 1.0 / math.sqrt(2.0))
_HAAR_HI = (-1.0 / math.sqrt(2.0), 1.0 / math.sqrt(2.0))

# Minimum samples for a meaningful multi-scale decomposition.
MIN_SAMPLES = 16
DEFAULT_LEVELS = 4
DEFAULT_THRESHOLD = 1.0

# Donoho-Johnstone universal threshold normalization factor.
def _universal_factor(n: int) -> float:
    return math.sqrt(2.0 * math.log(float(n)))


# A background spread below peak*_SIGMA_REL_FLOOR is float residue, not real
# variation (quantized/periodic baselines leave MAD at ~1e-16). Such scales
# fall back to population std before being judged.
_SIGMA_REL_FLOOR = 1e-9


def _is_finite_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) \
        and math.isfinite(float(v))


def _dilate(kernel: Sequence[float], level: int) -> List[float]:
    """Insert 2^(level-1)-1 zeros between taps (a-trous dilation)."""
    gap = (1 << (level - 1)) - 1
    out: List[float] = []
    for tap in kernel:
        out.append(tap)
        out.extend([0.0] * gap)
    return out


def _circular_conv(sig: Sequence[float], kernel: Sequence[float]) -> List[float]:
    """out[i] = sum_k kernel[k] * sig[(i - k) mod N] (circular boundary)."""
    n = len(sig)
    m = len(kernel)
    return [sum(kernel[k] * sig[(i - k) % n] for k in range(m))
            for i in range(n)]


def modwt_details(signal: Sequence[float], levels: int) -> List[List[float]]:
    """MODWT decomposition: returns [W_1, ..., W_levels] detail coefficient
    series (a-trous algorithm, circular boundaries). Raw transform, no
    fail-closed policy — callers enforce MIN_SAMPLES."""
    if not isinstance(levels, int) or isinstance(levels, bool) or levels < 1:
        raise ValueError(f"levels must be a positive int, got {levels!r}")
    w = [float(v) for v in signal]
    details: List[List[float]] = []
    for level in range(1, levels + 1):
        d = _circular_conv(w, _dilate(_HAAR_HI, level))
        details.append(d)
        w = _circular_conv(w, _dilate(_HAAR_LO, level))
    return details


def _median(vals: Sequence[float]) -> float:
    return statistics.median(vals)


def _mad(vals: Sequence[float]) -> float:
    """Median absolute deviation about the median."""
    m = _median(vals)
    return _median([abs(v - m) for v in vals])


def compute_mcav(signal: Sequence[float], levels: int) -> Dict[str, float]:
    """Mature Context Antigen Value = max over scales of
    (peak |W_j|) / (sigma_j * sqrt(2 ln N)), sigma_j = MAD(W_j)/0.6745.

    Per-scale robust normalization: each scale is judged against its own
    background spread, so coarse-scale drift (slow signal structure) cannot
    masquerade as a transient. Degenerate scales fall back from MAD to
    population std, then contribute nothing (no contrast, no anomaly).
    A fully constant decomposition yields MCAV 0.0.
    """
    n = len(signal)
    details = modwt_details(signal, levels)
    factor = _universal_factor(n)
    best = {"mcav": 0.0, "peak": 0.0, "sigma": 0.0, "scale": 0.0}
    for idx, coeffs in enumerate(details, start=1):
        peak = max(abs(c) for c in coeffs)
        if peak == 0.0:
            continue
        sigma = _mad(coeffs) / 0.6745
        if sigma <= peak * _SIGMA_REL_FLOOR:
            try:
                sigma = statistics.pstdev(coeffs)
            except statistics.StatisticsError:
                sigma = 0.0
        if sigma <= peak * _SIGMA_REL_FLOOR:
            continue  # no measurable background contrast at this scale
        ratio = peak / (sigma * factor)
        if ratio > best["mcav"]:
            best = {"mcav": ratio, "peak": peak, "sigma": sigma,
                    "scale": float(idx)}
    return {"mcav": best["mcav"], "peak": best["peak"], "sigma": best["sigma"],
            "levels": float(levels), "scale": best["scale"]}


def extract_signal(antigens: Sequence[Dict[str, Any]]) -> List[float]:
    """Pull the mDC time series from SovereignRuntime antigen records.

    Prefers the record's own "mDC" (sovereign_runtime computes
    mDC = 2*pamp + ds - 1.5*ss); recomputes from pamp/ds/ss when absent.
    Raises ValueError on malformed/non-finite records (fail closed upstream).
    """
    out: List[float] = []
    for i, rec in enumerate(antigens):
        if isinstance(rec, dict):
            if "mDC" in rec:
                v = rec["mDC"]
            elif "pamp" in rec and "ds" in rec:
                pamp, ds = rec["pamp"], rec["ds"]
                ss = rec.get("ss", 1.0)
                if not (_is_finite_number(pamp) and _is_finite_number(ds)
                        and _is_finite_number(ss)):
                    raise ValueError(f"antigen[{i}] non-finite pamp/ds/ss")
                v = 2.0 * float(pamp) + float(ds) - 1.5 * float(ss)
            else:
                raise ValueError(f"antigen[{i}] missing mDC/pamp/ds")
        elif _is_finite_number(rec):
            v = rec
        else:
            raise ValueError(f"antigen[{i}] malformed record: {type(rec).__name__}")
        if not _is_finite_number(v):
            raise ValueError(f"antigen[{i}] non-finite mDC: {v!r}")
        out.append(float(v))
    return out


def _fail_closed(reason: str, threshold: float, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    report = {"status": "FAIL_CLOSED", "pipeline": "MODWT-DCA",
              "verdict": "FAIL_CLOSED", "threshold": threshold, "reason": reason}
    if extra:
        report.update(extra)
    return report


def analyze(signal: Optional[Sequence[float]] = None, *,
            antigens: Optional[Sequence[Dict[str, Any]]] = None,
            threshold: float = DEFAULT_THRESHOLD,
            levels: int = DEFAULT_LEVELS) -> Dict[str, Any]:
    """Run the Ingest -> MODWT -> MCAV -> Threshold pipeline.

    Returns a report dict: status OK (with mcav + verdict BASAL|DANGER) or
    FAIL_CLOSED (never SAFE). Raises ValueError on invalid threshold/levels
    (programming errors fail loudly, inputs fail closed).
    """
    if not _is_finite_number(threshold) or float(threshold) <= 0.0:
        raise ValueError(f"threshold must be a positive finite number, got {threshold!r}")
    if not isinstance(levels, int) or isinstance(levels, bool) or levels < 1:
        raise ValueError(f"levels must be a positive int, got {levels!r}")
    threshold = float(threshold)

    if signal is None and antigens is None:
        return _fail_closed("NO_INPUT", threshold)
    if signal is not None and antigens is not None:
        return _fail_closed("AMBIGUOUS_INPUT", threshold)

    try:
        sig = list(signal) if signal is not None else extract_signal(antigens or [])
    except ValueError as e:
        return _fail_closed(f"MALFORMED_INPUT: {e}", threshold)

    n = len(sig)
    if n == 0:
        return _fail_closed("EMPTY_SIGNAL", threshold)
    if n < MIN_SAMPLES:
        return _fail_closed("INSUFFICIENT_SAMPLES", threshold,
                            {"n": n, "min_samples": MIN_SAMPLES})
    if not all(_is_finite_number(v) for v in sig):
        return _fail_closed("NON_FINITE_SIGNAL", threshold)

    eff_levels = min(levels, max(1, int(math.floor(math.log2(n)))))
    stats = compute_mcav(sig, eff_levels)
    mcav = stats["mcav"]
    verdict = "DANGER" if mcav > threshold else "BASAL"
    return {"status": "OK", "pipeline": "MODWT-DCA", "n": n,
            "levels": eff_levels, "mcav": round(mcav, 6),
            "peak": round(stats["peak"], 6), "sigma": round(stats["sigma"], 6),
            "scale": int(stats["scale"]),
            "threshold": threshold, "verdict": verdict}


def from_runtime(runtime: Any, *, threshold: float = DEFAULT_THRESHOLD,
                 levels: int = DEFAULT_LEVELS) -> Dict[str, Any]:
    """Analyze a live SovereignRuntime's antigen stream (public attribute)."""
    return analyze(antigens=list(getattr(runtime, "antigens", [])),
                   threshold=threshold, levels=levels)


def main(argv: Sequence[str]) -> int:
    """CLI: python3 modwt_dca_engine.py <antigens.json> — prints the report.

    The JSON file is a list of antigen records (dicts with mDC/pamp/ds/ss)
    or plain floats. Exit 0 only when status is OK.
    """
    import json
    if len(argv) != 1:
        print("usage: modwt_dca_engine.py <antigens.json>", flush=True)
        return 2
    try:
        with open(argv[0], "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, list):
            raise ValueError("input must be a JSON list")
    except (OSError, ValueError) as e:
        print(json.dumps(_fail_closed(f"INPUT_ERROR: {e}", DEFAULT_THRESHOLD)))
        return 1
    report = analyze(antigens=data)
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "OK" else 1


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv[1:]))
