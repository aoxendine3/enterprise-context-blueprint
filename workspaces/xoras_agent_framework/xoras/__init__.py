"""
XORAS Systems LLC — Agentic Environment & Governance Framework v2.4.0
Enterprise-grade multi-agent runtime, AST static security gating, MTPO lock-free concurrency,
Context Lineage Merkle DAG provenance receipts, SIEM exporters, and SOC2 compliance auditing.
"""

__version__ = "2.4.3"
__author__ = "XORAS Systems LLC"

from .config import XORASConfig
from .ast_security import ASTSecurityEngine, ASTScanResult
from .signer import CryptographicSigner, EvidenceReceipt
from .runtime import XORASAgentEnvironment
from .orchestrator import SwarmOrchestrator
from .exporters.siem_exporter import SIEMExporter
from .ipc.polyglot_ipc_bridge import PolyglotIPCBridge
from .compliance.soc2_auditor import SOC2ComplianceAuditor
from .tools.serpapi_client import XORASSerpAPIClient
from .mtpo import HexCellRing, HEXCELL_SLOTS, SagaState
from .merkle_dag import MerkleDAGNode, ContextLineageDAGEngine
from .agents import AgentCard, AgentRoster
from .council import CouncilOrchestrator, CouncilStep

def test() -> int:
    """Run bundled test suite directly from Python code."""
    import os
    import pytest
    tests_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests")
    return pytest.main([tests_dir, "-v"])


__all__ = [
    "XORASConfig",
    "ASTSecurityEngine",
    "ASTScanResult",
    "CryptographicSigner",
    "EvidenceReceipt",
    "XORASAgentEnvironment",
    "SwarmOrchestrator",
    "SIEMExporter",
    "PolyglotIPCBridge",
    "SOC2ComplianceAuditor",
    "XORASSerpAPIClient",
    "HexCellRing",
    "HEXCELL_SLOTS",
    "SagaState",
    "MerkleDAGNode",
    "ContextLineageDAGEngine",
    "AgentCard",
    "AgentRoster",
    "CouncilOrchestrator",
    "CouncilStep",
    "test",
]
