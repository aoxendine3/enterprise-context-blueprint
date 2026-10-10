"""
XORAS Systems LLC — R&D Breakthrough Prototype Engine Suite
Working prototypes for the 5 global paper-only AI concepts.
"""

from .smt_proof_engine import SMTProofEngine, SMTVerificationResult
from .epistemic_immune_swarm import EpistemicImmuneSwarm, ImmunocyteScanResult
from .topological_manifold_bridge import TopologicalManifoldBridge, ManifoldType
from .hardware_taint_lattice import HardwareTaintLattice, TaintState
from .zk_self_mutation_verifier import ZKSelfMutationVerifier, MutationProofResult

__all__ = [
    "SMTProofEngine",
    "SMTVerificationResult",
    "EpistemicImmuneSwarm",
    "ImmunocyteScanResult",
    "TopologicalManifoldBridge",
    "ManifoldType",
    "HardwareTaintLattice",
    "TaintState",
    "ZKSelfMutationVerifier",
    "MutationProofResult"
]
