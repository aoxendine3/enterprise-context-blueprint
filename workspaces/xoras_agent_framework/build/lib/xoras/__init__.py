"""
XORAS Systems LLC — Agentic Environment & Governance Framework
Enterprise-grade multi-agent runtime, AST static security gating, cryptographic provenance receipts, SIEM exporters, and SOC2 compliance auditing.
"""

__version__ = "2.3.0"
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
    "XORASSerpAPIClient"
]
