"""
XORAS R&D Prototype 3: Dynamic Topological Manifold Memory Switching (Fail-Closed Remediated)
Dynamically morphs memory geometry between Poincaré Hyperbolic, Euclidean, and Spherical metric spaces.
Remediates BBQ-06 (Boundary clamping), BBQ-07 (NaN/Inf handling), and BBQ-08 (Spherical vector normalization).
"""

import math
from enum import Enum
from dataclasses import dataclass
from typing import List

class ManifoldType(Enum):
    POINCARE_HYPERBOLIC = "Poincare_Hyperbolic_18432D"
    EUCLIDEAN = "Euclidean_Standard_Flat"
    SPHERICAL = "Spherical_Periodic_Curvature"

@dataclass
class DynamicEmbeddingResult:
    manifold: ManifoldType
    curvature: float
    vector_dimension: int
    distance: float

class TopologicalManifoldBridge:
    def __init__(self, default_hyperbolic_dim: int = 18432):
        self.default_hyperbolic_dim = default_hyperbolic_dim

    def determine_optimal_manifold(self, data_type: str, depth_hierarchy: int) -> ManifoldType:
        if depth_hierarchy > 2 or data_type in ("ast_tree", "taxonomy", "codebase_graph", "lineage_dag"):
            return ManifoldType.POINCARE_HYPERBOLIC
        elif data_type in ("time_series", "cyclical_metrics", "periodic_pulse"):
            return ManifoldType.SPHERICAL
        else:
            return ManifoldType.EUCLIDEAN

    def compute_distance(self, u: List[float], v: List[float], manifold: ManifoldType) -> DynamicEmbeddingResult:
        if len(u) != len(v):
            raise ValueError(f"Dimension mismatch: len(u)={len(u)} != len(v)={len(v)}")
        if any(math.isnan(x) or math.isinf(x) for x in u + v):
            raise ValueError("Input vectors contain NaN or Inf values")

        if manifold == ManifoldType.POINCARE_HYPERBOLIC:
            sq_norm_u = sum(x**2 for x in u)
            sq_norm_v = sum(x**2 for x in v)
            if sq_norm_u >= 1.0 or sq_norm_v >= 1.0:
                raise ValueError(f"Poincaré boundary violation: ||u||^2={sq_norm_u:.4f}, ||v||^2={sq_norm_v:.4f} must be < 1.0")

            sq_dist = sum((x - y)**2 for x, y in zip(u, v))
            denom = (1.0 - sq_norm_u) * (1.0 - sq_norm_v)
            val = 1.0 + 2.0 * sq_dist / denom
            dist = math.acosh(max(1.0, val))
            curvature = -1.0
            dim = self.default_hyperbolic_dim
        elif manifold == ManifoldType.SPHERICAL:
            norm_u = math.sqrt(sum(x**2 for x in u))
            norm_v = math.sqrt(sum(x**2 for x in v))
            if norm_u == 0 or norm_v == 0:
                raise ValueError("Zero vector passed to spherical metric")
            u_norm = [x / norm_u for x in u]
            v_norm = [x / norm_v for x in v]
            dot_prod = sum(x * y for x, y in zip(u_norm, v_norm))
            dist = math.acos(max(-1.0, min(1.0, dot_prod)))
            curvature = 1.0
            dim = len(u)
        else:
            dist = math.sqrt(sum((x - y)**2 for x, y in zip(u, v)))
            curvature = 0.0
            dim = len(u)

        return DynamicEmbeddingResult(
            manifold=manifold,
            curvature=curvature,
            vector_dimension=dim,
            distance=round(dist, 6)
        )
