# mcp_suite_client.py
# Sovereign client interface for Anthony's superanjox/ai_coding MCP Suite Catalog
import os
import json
from pathlib import Path
from typing import Dict, Any, List

CATALOG_PATH = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/core/products/mcp/superanjox_ai_coding_catalog.json")

class SovereignMCPSuite:
    def __init__(self, catalog_path: Path = CATALOG_PATH):
        self.catalog_path = catalog_path
        self._load_catalog()

    def _load_catalog(self):
        if not self.catalog_path.exists():
            self.catalog = {"servers": []}
            return
        with open(self.catalog_path, "r") as f:
            self.catalog = json.load(f)

    def list_servers(self) -> List[Dict[str, Any]]:
        servers = []
        for s in self.catalog.get("servers", []):
            snap = s.get("snapshot", {}).get("server", {})
            servers.append({
                "name": snap.get("name"),
                "title": snap.get("title"),
                "image": s.get("image"),
                "tools_count": len(snap.get("tools", [])),
                "tools": [t.get("name") for t in snap.get("tools", [])]
            })
        return servers

    def get_server_tools(self, server_name: str) -> List[Dict[str, Any]]:
        for s in self.catalog.get("servers", []):
            snap = s.get("snapshot", {}).get("server", {})
            if snap.get("name") == server_name:
                return snap.get("tools", [])
        return []

    def route_tool_to_citizen(self, tool_name: str) -> str:
        # Route MCP tools to specialized sovereign citizen sandboxes
        if tool_name in ["search_papers", "download_paper", "read_paper"]:
            return "clara" # Clara: Deep scientific research
        elif tool_name in ["perplexity_ask", "perplexity_reason", "perplexity_research"]:
            return "counselor" # Counselor: Real-time web intelligence
        elif tool_name.startswith("kubectl_") or tool_name in ["exec_in_pod", "install_helm_chart"]:
            return "axlon" # Axlon: Substrate & cluster infrastructure
        elif tool_name.startswith("get_address_") or tool_name.startswith("rpc_"):
            return "sophia" # Sophia: Immutable on-chain Bitcoin provenance
        return "maxx" # Default SSOT orchestrator

if __name__ == "__main__":
    suite = SovereignMCPSuite()
    print("Loaded Sovereign MCP Suite:", len(suite.list_servers()), "servers.")
    for s in suite.list_servers():
        print(f" - {s['title']}: {s['tools_count']} tools")
