#!/usr/bin/env python3
"""
Poincaré Semantic Drift Gate
============================

A deterministic, dependency-free state-transition gate for governed memory
writes. It answers one question:

    "Is this candidate value a bounded move away from the accepted baseline
     for the same key, or is it a semantic jump?"

The metric is the Poincaré disk geodesic distance

    d_H(u, v) = arccosh( 1 + 2 ||u - v||² / ((1 - ||u||²)(1 - ||v||²)) )

Two embeddings are used, and each is labelled honestly.

``scalar``
    A single finite real number is mapped to a log-radial coordinate

        t = ln|x| / LOG_SCALE ,   r = tanh(t)

    so that, for two values in the same sign class, ``d_H == |ln(a / b)|``
    exactly. ``LOG_SCALE = 2`` and an absolute ceiling of ``0.5`` mean an
    in-place numeric write may change a value by at most ``e^0.5 ≈ 1.65×``.
    The bound is scale-invariant: it behaves the same for 0.5, 18,432, or 3e9.

    A change of sign class (positive / negative / zero) is treated as maximum
    drift. The 1-D radial coordinate cannot distinguish ``+x`` from ``-x``
    without a collision, so the sign is checked explicitly rather than folded
    into the metric.

``text``
    A string is normalised (NFKC, case-folded, non-alphanumerics removed),
    embedded with signed character-trigram hashing into ``TEXT_DIM``
    dimensions, L2-normalised, and scaled to norm ``TEXT_NORM``. This is a
    *lexical* embedding, not a neural one.

    The text policy is deliberately absolute: a text value that differs from
    its baseline after cosmetic normalisation is a semantic transition, not a
    refinement, and is vetoed. Legitimate text transitions are published under
    a new key version, which is auditable. This removes the need for an
    arbitrary "semantic similarity" threshold that would let a short payload
    swap slip past a long one.

Relationship to parts that already existed
------------------------------------------
This module is an adapter, not a new manifold. The repository already had:

- ``labs/workspaces/sovra_nexus/sovra_core/poincare_hypergraph.py`` —
  ``PoincareManifold.geodesic_distance``, the canonical n-dimensional metric.
  The formula here is identical, and
  ``tests/test_governor_poincare_gate.py::test_parity_with_canonical_sovra_manifold``
  asserts numerical parity. It is not imported at runtime because its
  ``1e-6`` boundary clip silently collapses large-magnitude states, which is
  unacceptable for a fail-closed gate.
- ``core/ops/native/zig/sovra_simd.zig`` — ``sovra_simd_poincare_distance_f32``.
  Not used: it is f32 and requires a compiled shared object, while the
  governor must run correctly with no build artifacts. The Zig path remains
  appropriate for bulk offline scoring.
- ``agents/citizens/aurelius/aurelius_invariant_kernel.py`` — a per-citizen
  scalar anchor sentry with a fixed genesis value. This module generalises
  that idea to the governed-memory write path: arbitrary keys, two embedding
  modes, and fail-closed receipts.

What did not exist was the part that matters for the defect: an embedding and
a fail-closed policy attached to ``evaluate_write_candidate``. That is what
this module adds.

Fail-closed contract
--------------------
``evaluate_transition`` never raises. Every failure mode — unembeddable value,
NaN/inf, empty input, disk-boundary overflow, internal exception — returns a
``VETO`` decision with a machine-readable reason. The governor treats anything
other than an explicit ``PASS``/``ANCHOR`` as a hard veto.

A first write for a key is an ``ANCHOR``: there is no baseline to drift from.
That is how a state machine starts, not a bypass. A *forged* supersede claim
with no baseline is rejected by the governor before the gate is consulted.
"""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Optional

__all__ = [
    "GateDecision",
    "GateResult",
    "GateError",
    "poincare_distance",
    "poincare_max_distance",
    "embed_value",
    "evaluate_transition",
    "normalise_text",
    "SCALAR_LOG_SCALE",
    "MAX_SCALAR_JUMP",
    "MAX_TEXT_JUMP",
    "TEXT_DIM",
    "TEXT_NORM",
]

# Scalar mode: d_H == |ln(a/b)| for same-sign values.
SCALAR_LOG_SCALE: float = 2.0
# d_H ceiling for a numeric in-place change. 0.5 == at most 1.65x.
MAX_SCALAR_JUMP: float = 0.5
# Text mode: only cosmetic equivalence is permitted in place.
MAX_TEXT_JUMP: float = 0.0

TEXT_DIM: int = 64
TEXT_NORM: float = 0.5
TEXT_MAX_CHARS: int = 4096
_MAX_RADIUS: float = 1.0 - 1e-12

_NON_ALNUM = re.compile(r"[^0-9a-z]+", re.UNICODE)


class GateError(ValueError):
    """A candidate could not be embedded into the Poincaré disk."""


@dataclass(frozen=True)
class GateDecision:
    PASS = "PASS"
    VETO = "VETO"
    ANCHOR = "ANCHOR"


@dataclass(frozen=True)
class GateResult:
    decision: str
    mode: str
    reason: str
    distance: Optional[float]
    max_distance: Optional[float]
    relative_distance: Optional[float]
    baseline_value_repr: Optional[str]
    candidate_value_repr: Optional[str]

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def accepted(self) -> bool:
        return self.decision in (GateDecision.PASS, GateDecision.ANCHOR)


def _norm_sq(vec: Iterable[float]) -> float:
    return math.fsum(x * x for x in vec)


def poincare_distance(u: tuple[float, ...], v: tuple[float, ...]) -> float:
    """Geodesic distance between two points strictly inside the unit ball."""
    if len(u) != len(v):
        raise GateError(f"DIMENSION_MISMATCH: {len(u)} != {len(v)}")
    nu = _norm_sq(u)
    nv = _norm_sq(v)
    if not (math.isfinite(nu) and math.isfinite(nv)):
        raise GateError("NON_FINITE_NORM")
    if nu >= 1.0 or nv >= 1.0:
        raise GateError("OUTSIDE_DISK")
    diff = math.fsum((a - b) ** 2 for a, b in zip(u, v))
    denom = (1.0 - nu) * (1.0 - nv)
    if denom <= 0.0:
        raise GateError("DEGENERATE_DENOMINATOR")
    arg = 1.0 + 2.0 * diff / denom
    if not math.isfinite(arg):
        raise GateError("NON_FINITE_ARGUMENT")
    return math.acosh(max(1.0, arg))


def poincare_max_distance(u: tuple[float, ...], v: tuple[float, ...]) -> float:
    """Largest distance two points with the given norms can have (antipodal)."""
    nu = math.sqrt(_norm_sq(u))
    nv = math.sqrt(_norm_sq(v))
    if nu >= 1.0 or nv >= 1.0:
        raise GateError("OUTSIDE_DISK")
    denom = (1.0 - nu * nu) * (1.0 - nv * nv)
    if denom <= 0.0:
        raise GateError("DEGENERATE_DENOMINATOR")
    arg = 1.0 + 2.0 * (nu + nv) ** 2 / denom
    return math.acosh(max(1.0, arg))


def _as_finite_float(value: Any) -> Optional[float]:
    """Return a finite float for numeric-looking values, else None."""
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        f = float(value)
        return f if math.isfinite(f) else None
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        try:
            f = float(s)
        except (TypeError, ValueError):
            return None
        return f if math.isfinite(f) else None
    return None


def _sign_class(x: float) -> int:
    return (x > 0.0) - (x < 0.0)


def _embed_scalar(x: float) -> tuple[float, ...]:
    if not math.isfinite(x):
        raise GateError("NON_FINITE_SCALAR")
    if x == 0.0:
        return (0.0,)
    t = math.log(abs(x)) / SCALAR_LOG_SCALE
    r = math.tanh(t)
    r = max(-_MAX_RADIUS, min(_MAX_RADIUS, r))
    return (r,)


def normalise_text(text: str) -> str:
    """
    Fold cosmetic differences so they cannot masquerade as semantic drift.

    NFKC, case-fold, and drop every character that is not a Latin letter or
    digit. ``"Port = 8080"``, ``"port=8080"`` and ``"port 8080"`` all collapse
    to ``"port8080"``. This is intentionally aggressive; a value whose folded
    form changes is a value whose meaning changed.
    """
    s = unicodedata.normalize("NFKC", text)[:TEXT_MAX_CHARS].casefold()
    return _NON_ALNUM.sub("", s)


def _text_tokens(text: str) -> Iterable[str]:
    s = normalise_text(text)
    padded = f"\x02{s}\x03"
    if len(padded) < 3:
        yield padded
        return
    for i in range(len(padded) - 2):
        yield padded[i : i + 3]


def _embed_text(text: str) -> tuple[float, ...]:
    if not isinstance(text, str):
        raise GateError("NON_STRING_VALUE")
    if not normalise_text(text):
        raise GateError("EMPTY_VALUE")
    buckets = [0.0] * TEXT_DIM
    for token in _text_tokens(text):
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        idx = int.from_bytes(digest[:4], "big") % TEXT_DIM
        sign = 1.0 if digest[4] & 1 else -1.0
        buckets[idx] += sign
    norm = math.sqrt(math.fsum(b * b for b in buckets))
    if norm == 0.0:
        raise GateError("DEGENERATE_EMBEDDING")
    scale = TEXT_NORM / norm
    vec = tuple(b * scale for b in buckets)
    if not all(math.isfinite(c) for c in vec):
        raise GateError("NON_FINITE_EMBEDDING")
    return vec


def embed_value(value: Any) -> tuple[str, tuple[float, ...]]:
    """
    Map a value into the Poincaré disk.

    Returns ``(mode, vector)``. Raises :class:`GateError` when the value has no
    faithful embedding.
    """
    if value is None:
        raise GateError("NULL_VALUE")
    numeric = _as_finite_float(value)
    if numeric is not None:
        return "scalar", _embed_scalar(numeric)
    if not isinstance(value, str):
        raise GateError(f"UNSUPPORTED_TYPE: {type(value).__name__}")
    return "text", _embed_text(value)


def _repr_value(value: Any, limit: int = 120) -> str:
    if value is None:
        return "None"
    if isinstance(value, str):
        s = value if len(value) <= limit else value[:limit] + f"...(+{len(value) - limit})"
        return repr(s)
    return repr(value)


def evaluate_transition(
    baseline_value: Any,
    candidate_value: Any,
    *,
    has_baseline: bool = True,
) -> GateResult:
    """
    Evaluate a candidate against the accepted baseline for the same key.

    Never raises. Failure to evaluate is a VETO, not a pass.
    """
    try:
        if not has_baseline:
            mode, _ = embed_value(candidate_value)
            return GateResult(
                decision=GateDecision.ANCHOR,
                mode=mode,
                reason="NO_BASELINE_ANCHOR",
                distance=None,
                max_distance=None,
                relative_distance=None,
                baseline_value_repr=None,
                candidate_value_repr=_repr_value(candidate_value),
            )

        try:
            baseline_mode, u = embed_value(baseline_value)
            candidate_mode, v = embed_value(candidate_value)
        except GateError as exc:
            return GateResult(
                decision=GateDecision.VETO,
                mode="unembeddable",
                reason=str(exc),
                distance=None,
                max_distance=None,
                relative_distance=None,
                baseline_value_repr=_repr_value(baseline_value),
                candidate_value_repr=_repr_value(candidate_value),
            )

        # A mode switch (number <-> text) is a representation change and is
        # treated as maximal drift. It may not slip through because both sides
        # happen to embed.
        if baseline_mode != candidate_mode:
            return GateResult(
                decision=GateDecision.VETO,
                mode=f"{baseline_mode}->{candidate_mode}",
                reason="EMBEDDING_MODE_SWITCH",
                distance=None,
                max_distance=None,
                relative_distance=1.0,
                baseline_value_repr=_repr_value(baseline_value),
                candidate_value_repr=_repr_value(candidate_value),
            )

        if baseline_mode == "scalar":
            a = _as_finite_float(baseline_value)
            b = _as_finite_float(candidate_value)
            if a is None or b is None:
                raise GateError("NON_NUMERIC_IN_SCALAR_MODE")
            if _sign_class(a) != _sign_class(b):
                return GateResult(
                    decision=GateDecision.VETO,
                    mode="scalar",
                    reason="SIGN_DISCONTINUITY",
                    distance=None,
                    max_distance=None,
                    relative_distance=1.0,
                    baseline_value_repr=_repr_value(baseline_value),
                    candidate_value_repr=_repr_value(candidate_value),
                )

        distance = poincare_distance(u, v)
        max_distance = poincare_max_distance(u, v)
        relative = 0.0 if max_distance <= 0.0 else distance / max_distance

        if baseline_mode == "scalar":
            limit = MAX_SCALAR_JUMP
            label = "SCALAR_JUMP"
        else:
            limit = MAX_TEXT_JUMP
            label = "TEXT_VALUE_MUTATION"

        decision = GateDecision.VETO if distance > limit else GateDecision.PASS
        reason = (
            f"{label} d_H={distance:.4f} > {limit}"
            if decision == GateDecision.VETO
            else "WITHIN_GEODESIC_BOUND"
        )
        return GateResult(
            decision=decision,
            mode=baseline_mode,
            reason=reason,
            distance=round(distance, 6),
            max_distance=round(max_distance, 6),
            relative_distance=round(relative, 6),
            baseline_value_repr=_repr_value(baseline_value),
            candidate_value_repr=_repr_value(candidate_value),
        )
    except Exception as exc:  # noqa: BLE001 - fail closed, never raise
        return GateResult(
            decision=GateDecision.VETO,
            mode="error",
            reason=f"GATE_ERROR: {type(exc).__name__}: {exc}",
            distance=None,
            max_distance=None,
            relative_distance=None,
            baseline_value_repr=_repr_value(baseline_value),
            candidate_value_repr=_repr_value(candidate_value),
        )
