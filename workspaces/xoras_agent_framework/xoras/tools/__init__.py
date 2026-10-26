"""
=============================================================================
XORAS UNIFIED SOVEREIGN TOOL REGISTRY
Path: workspaces/xoras_agent_framework/xoras/tools/__init__.py
Standards: NIST SP 800-53 Rev. 5, NASA Software Safety Standard (Fail-Closed)
Expansion: 2 legacy tools -> 7 comprehensive sovereign tools (+250% expansion)
=============================================================================
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from xoras.tools.serpapi_client import XORASSerpAPIClient
from xoras.tools.model_manifest import ModelManifestScanner
from xoras.tools.native_system_probe import NativeSystemProbe
from xoras.tools.cryptographic_vault import CryptographicVault
from xoras.tools.code_sandbox_runner import CodeSandboxRunner
from xoras.tools.epistemic_provenance_store import EpistemicProvenanceStore
from xoras.tools.network_airgap_guard import NetworkAirgapGuard


@dataclass(frozen=True)
class ToolDescriptor:
    name: str
    category: str
    description: str
    capabilities: List[str]
    is_sandboxed: bool
    requires_network: bool


class SovereignToolRegistry:
    """
    Central sovereign registry for agent tools with capability verification,
    telemetry auditing, and fail-closed dispatching.
    """
    SCHEMA_VERSION = "xoras.tool_registry.v1"

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDescriptor] = {}
        self._invokers: Dict[str, Callable[..., Any]] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        # 1. Native System Probe
        probe_inst = NativeSystemProbe()
        self.register_tool(
            descriptor=ToolDescriptor(
                name="native_system_probe",
                category="HARDWARE_KERNEL_TELEMETRY",
                description="Queries physical Apple Silicon M4 unified memory, CPU, and storage headroom cleanly.",
                capabilities=["read_only", "sysctl", "statvfs"],
                is_sandboxed=True,
                requires_network=False,
            ),
            invoker=probe_inst.as_dict,
        )

        # 2. Cryptographic Vault
        vault_inst = CryptographicVault()
        self.register_tool(
            descriptor=ToolDescriptor(
                name="cryptographic_vault",
                category="CRYPTOGRAPHY_INTEGRITY",
                description="Signs and verifies payloads via HMAC-SHA256, computes Merkle roots, prevents replay.",
                capabilities=["hmac_sha256", "merkle_tree", "anti_replay"],
                is_sandboxed=True,
                requires_network=False,
            ),
            invoker=lambda action, *args: getattr(vault_inst, action)(*args),
        )

        # 3. Code Sandbox Runner
        sandbox_inst = CodeSandboxRunner(timeout_sec=3.0)
        self.register_tool(
            descriptor=ToolDescriptor(
                name="code_sandbox_runner",
                category="EXECUTION_SANDBOX",
                description="Runs Python verification snippets in isolated AST-screened subprocess containers.",
                capabilities=["ast_screening", "process_isolation", "timeout_fencing"],
                is_sandboxed=True,
                requires_network=False,
            ),
            invoker=lambda code: asdict(sandbox_inst.run_snippet(code)),
        )

        # 4. Epistemic Provenance Store
        epistemic_inst = EpistemicProvenanceStore()
        self.register_tool(
            descriptor=ToolDescriptor(
                name="epistemic_provenance_store",
                category="KNOWLEDGE_LEDGER",
                description="Maintains hash-chained, ethically-scored assertions to prevent memory drift.",
                capabilities=["hash_chain", "ethical_scoring", "fact_retrieval"],
                is_sandboxed=True,
                requires_network=False,
            ),
            invoker=lambda action, *args, **kwargs: getattr(epistemic_inst, action)(*args, **kwargs),
        )

        # 5. Network Airgap Guard
        airgap_inst = NetworkAirgapGuard()
        self.register_tool(
            descriptor=ToolDescriptor(
                name="network_airgap_guard",
                category="BOUNDARY_SECURITY",
                description="Enforces local-first network boundaries, blocking external telemetry and cloud meters.",
                capabilities=["local_first_routing", "subnet_allowlist", "telemetry_block"],
                is_sandboxed=True,
                requires_network=False,
            ),
            invoker=lambda target: asdict(airgap_inst.audit_destination(target)),
        )

        # 6. Model Manifest Scanner
        scanner_inst = ModelManifestScanner()
        self.register_tool(
            descriptor=ToolDescriptor(
                name="model_manifest_scanner",
                category="SUPPLY_CHAIN_INTEGRITY",
                description="Audits local Ollama cluster models for ghost manifests, rug-pulls, and poisoned templates.",
                capabilities=["read_only", "supply_chain_audit", "template_screening"],
                is_sandboxed=True,
                requires_network=True,
            ),
            invoker=lambda *args, **kwargs: scanner_inst.scan(*args, **kwargs),
        )

        # 7. SerpApi Client (External Search with key gating)
        serpapi_inst = XORASSerpAPIClient()
        self.register_tool(
            descriptor=ToolDescriptor(
                name="serpapi_client",
                category="EXTERNAL_RESEARCH",
                description="Conducts controlled web research when explicitly configured.",
                capabilities=["search", "news", "citations"],
                is_sandboxed=True,
                requires_network=True,
            ),
            invoker=lambda q, **kw: serpapi_inst.search(q, **kw),
        )

    def register_tool(self, descriptor: ToolDescriptor, invoker: Callable[..., Any]) -> None:
        """Register a new tool with capability descriptor and dispatch invoker."""
        self._tools[descriptor.name] = descriptor
        self._invokers[descriptor.name] = invoker

    def list_tools(self) -> List[ToolDescriptor]:
        """Return list of all registered tools."""
        return list(self._tools.values())

    def execute_tool(self, tool_name: str, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Execute tool safely with timing receipt and error handling."""
        if tool_name not in self._tools:
            return {
                "status": "TOOL_NOT_FOUND",
                "tool_name": tool_name,
                "error": f"Tool '{tool_name}' is not registered in SovereignToolRegistry.",
            }

        descriptor = self._tools[tool_name]
        invoker = self._invokers[tool_name]

        t0 = time.perf_counter()
        try:
            result = invoker(*args, **kwargs)
            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            return {
                "status": "SUCCESS",
                "tool_name": tool_name,
                "category": descriptor.category,
                "execution_time_ms": elapsed_ms,
                "result": result,
            }
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            return {
                "status": "EXECUTION_ERROR",
                "tool_name": tool_name,
                "category": descriptor.category,
                "execution_time_ms": elapsed_ms,
                "error": str(e),
            }


__all__ = [
    "SovereignToolRegistry",
    "ToolDescriptor",
    "XORASSerpAPIClient",
    "ModelManifestScanner",
    "NativeSystemProbe",
    "CryptographicVault",
    "CodeSandboxRunner",
    "EpistemicProvenanceStore",
    "NetworkAirgapGuard",
]
