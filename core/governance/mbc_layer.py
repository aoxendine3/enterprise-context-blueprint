#!/usr/bin/env python3
"""
MBC-Core extensions: Epitope contrastive matching + SC-Layer topological shield.
Adds to sovereign_runtime.py the two genuinely new mechanisms in the
Monotonic Bio-Cognitive Core spec, implemented without theater:

  1. Transferable Epitope (Intent, Mechanism, Goal Impact) with field coverage
     s_i, s_m, s_g in [0,1] and contrastive exclusion G(A, alpha):
         C(A,alpha) = (s_i+s_m+s_g)/3 * G(A,alpha)
     G=0 when a must_not_have exclusion fires -> confidence zero.

  2. SC-Layer: convert safe-ordering constraints Phi into a directed OrderGraph
     (V,E); if a proposed action vector violates ordering, compute a topological
     permutation into compliance. FAIL CLOSED on cycles (no valid ordering).

The spec's "speculative in-place writes + saga inverses" is NOT adopted: the
critique proved it is an uncompensated dirty write. CoW two-phase commit in
sovereign_runtime.py stays the write path.

STATUS: production core with empirical tests; formal proof not attached.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
import heapq


# ---------------------------------------------------------------------------
# 1. Transferable epitope + hierarchical contrastive matching
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Epitope:
    intent: str
    mechanism: str
    goal_impact: str


@dataclass
class EpitopeAntibody:
    antibody_id: str
    synopsis: str
    epitope: Epitope
    must_have: Callable[[Epitope], bool]       # H_A
    must_not_have: Callable[[Epitope], bool]   # N_A -> G=0
    threshold: float
    remediation: str
    confidence: float = 0.0

    def coverage(self, alpha: Epitope) -> Tuple[float, float, float]:
        si = 1.0 if self.epitope.intent == alpha.intent else 0.0
        sm = 1.0 if self.epitope.mechanism == alpha.mechanism else 0.0
        sg = 1.0 if self.epitope.goal_impact == alpha.goal_impact else 0.0
        return si, sm, sg

    def match(self, alpha: Epitope) -> float:
        si, sm, sg = self.coverage(alpha)
        g = 0.0 if self.must_not_have(alpha) else (1.0 if self.must_have(alpha) else 0.0)
        return ((si + sm + sg) / 3.0) * g

    def triggers(self, alpha: Epitope) -> bool:
        self.confidence = self.match(alpha)
        return self.confidence >= self.threshold


class EpitopeRegistry:
    def __init__(self):
        self._abs: List[EpitopeAntibody] = []

    def register(self, ab: EpitopeAntibody) -> None:
        self._abs.append(ab)

    def inspect(self, alpha: Epitope) -> Tuple[bool, Optional[EpitopeAntibody]]:
        for ab in self._abs:
            if ab.triggers(alpha):
                return True, ab
        return False, None


# ---------------------------------------------------------------------------
# 2. SC-Layer topological shield
# ---------------------------------------------------------------------------
class OrderCycle(Exception):
    pass


class SCLayer:
    """Converts safe-ordering constraints Phi into an OrderGraph and permutes
    an action vector into compliance via Kahn topological sort."""

    def __init__(self, edges: List[Tuple[str, str]]):
        self.vertices: set = set()
        for a, b in edges:
            self.vertices.add(a); self.vertices.add(b)
        self.edges = list(edges)

    def topo_sort(self) -> List[str]:
        indeg = {v: 0 for v in self.vertices}
        adj: Dict[str, List[str]] = {v: [] for v in self.vertices}
        for a, b in self.edges:
            adj[a].append(b); indeg[b] += 1
        heap = [v for v in self.vertices if indeg[v] == 0]
        heapq.heapify(heap)
        order = []
        while heap:
            v = heapq.heappop(heap)
            order.append(v)
            for w in adj[v]:
                indeg[w] -= 1
                if indeg[w] == 0:
                    heapq.heappush(heap, w)
        if len(order) != len(self.vertices):
            raise OrderCycle("OrderGraph contains a cycle; no compliant permutation exists")
        return order

    def shield(self, proposed: List[str]) -> List[str]:
        """Permute proposed action vector into topological compliance."""
        order = self.topo_sort()
        rank = {v: i for i, v in enumerate(order)}
        unknown = [a for a in proposed if a not in rank]
        if unknown:
            raise ValueError(f"Action outside OrderGraph: {unknown}")
        return sorted(proposed, key=lambda a: rank[a])

    def compliant(self, proposed: List[str]) -> bool:
        """Check whether a vector already respects the partial order."""
        order = self.topo_sort()
        pos = {v: i for i, v in enumerate(proposed)}
        if len(pos) != len(proposed):
            return False
        for a, b in self.edges:
            if pos[a] > pos[b]:
                return False
        return True
