#!/usr/bin/env python3
"""
===============================================================================
XORAS::OS - UNIFIED CLOUD INFRASTRUCTURE MCP SERVER (v1.0.0)
===============================================================================
Exposes Qdrant, Upstash, Cloudflare R2, and Neon Postgres MCP tools to Swarm.
Author: The Lead 9 Council (Maxx, Clara, Vance, John, DAXX)
===============================================================================
"""

import os
import sys
import json
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qdrant_client import SovereignQdrantClient
from upstash_client import SovereignUpstashClient
from cloudflare_r2_client import SovereignCloudflareR2Client
from neon_postgres_client import SovereignNeonPostgresClient

# Additional Memory & Substrate imports
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../AI_Core/Xoras_Project/xoras-core/Source"))
LABS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../labs/workspaces/sovra_nexus"))
sys.path.insert(0, SRC_DIR)
sys.path.insert(0, LABS_DIR)

try:
    from xoras_memory_fabric import get_memory_fabric
    HAS_MEMORY_FABRIC = True
except Exception:
    HAS_MEMORY_FABRIC = False

try:
    from sovra_core.poincare_hypergraph import PoincareManifold
    from sovra_core.hexcell_memory import HexCell, HexCellEngine
    HAS_POINCARE_GRAPH = True
except Exception:
    HAS_POINCARE_GRAPH = False

try:
    import lancedb
    HAS_LANCEDB = True
except Exception:
    HAS_LANCEDB = False

VAULT_DIR = os.getenv("VAULT_DIR", os.path.expanduser("~/Desktop/SSOT_Agentic_Brain/data_center/research/lancedb_vault"))

class UnifiedCloudMCPServer:
    def __init__(self):
        self.qdrant = SovereignQdrantClient()
        self.upstash = SovereignUpstashClient()
        self.r2 = SovereignCloudflareR2Client()
        self.neon = SovereignNeonPostgresClient()
        self.memory_fabric = get_memory_fabric() if HAS_MEMORY_FABRIC else None
        self.poincare_manifold = PoincareManifold(dim=16) if HAS_POINCARE_GRAPH else None

        self.tools = {
            "qdrant_create_collection": self.qdrant_create_collection,
            "qdrant_search_vectors": self.qdrant_search_vectors,
            "upstash_redis_set": self.upstash_redis_set,
            "upstash_redis_get": self.upstash_redis_get,
            "upstash_qstash_publish": self.upstash_qstash_publish,
            "r2_upload_artifact": self.r2_upload_artifact,
            "r2_list_artifacts": self.r2_list_artifacts,
            "neon_execute_sql": self.neon_execute_sql,
            "neon_log_provenance": self.neon_log_provenance,
            "lancedb_vault_search": self.lancedb_vault_search,
            "graphrag_hypergraph_query": self.graphrag_hypergraph_query,
            "memory_fabric_hydrate": self.memory_fabric_hydrate
        }

    def qdrant_create_collection(self, distance: str = "Cosine") -> str:
        return json.dumps(self.qdrant.create_collection(distance), indent=2)

    def qdrant_search_vectors(self, query_vector: List[float], limit: int = 5) -> str:
        return json.dumps(self.qdrant.search_vectors(query_vector, limit), indent=2)

    def upstash_redis_set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> str:
        return json.dumps(self.upstash.redis_set(key, value, ttl_seconds), indent=2)

    def upstash_redis_get(self, key: str) -> str:
        return json.dumps(self.upstash.redis_get(key), indent=2)

    def upstash_qstash_publish(self, destination_url: str, message: Dict[str, Any], delay_seconds: int = 0) -> str:
        return json.dumps(self.upstash.qstash_publish_job(destination_url, message, delay_seconds), indent=2)

    def r2_upload_artifact(self, file_path: str, object_key: Optional[str] = None) -> str:
        return json.dumps(self.r2.upload_artifact(file_path, object_key), indent=2)

    def r2_list_artifacts(self, prefix: str = "") -> str:
        return json.dumps(self.r2.list_artifacts(prefix), indent=2)

    def neon_execute_sql(self, query: str, params: Optional[List[Any]] = None) -> str:
        return json.dumps(self.neon.execute_sql(query, params), indent=2)

    def neon_log_provenance(self, node_id: str, session_id: str, merkle_root: str, sha256_hash: str) -> str:
        return json.dumps(self.neon.log_provenance_record(node_id, session_id, merkle_root, sha256_hash), indent=2)

    def lancedb_vault_search(self, query_text: str = "", limit: int = 5) -> str:
        if not HAS_LANCEDB:
            return json.dumps({"status": "error", "message": "LanceDB module not installed"}, indent=2)
        try:
            os.makedirs(VAULT_DIR, exist_ok=True)
            db = lancedb.connect(VAULT_DIR)
            tables = db.table_names() if hasattr(db, "table_names") else db.list_tables()
            return json.dumps({
                "status": "success",
                "vault_dir": VAULT_DIR,
                "tables": list(tables),
                "query": query_text,
                "limit": limit
            }, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "vault_dir": VAULT_DIR, "error": str(e)}, indent=2)

    def graphrag_hypergraph_query(self, node_id: int = 1, top_k: int = 5) -> str:
        if not HAS_POINCARE_GRAPH or not self.poincare_manifold:
            return json.dumps({"status": "error", "message": "Poincaré Hypergraph not initialized"}, indent=2)
        try:
            u = [0.01 * node_id] * 16
            v = [0.02 * node_id] * 16
            dist = self.poincare_manifold.geodesic_distance(u, v)
            return json.dumps({
                "status": "success",
                "engine": "PoincareHypergraph_16D",
                "node_id": node_id,
                "geodesic_distance": round(dist, 6),
                "top_k": top_k
            }, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)}, indent=2)

    def memory_fabric_hydrate(self, agent_id: str = "maxx", query: str = "", mode: str = "scrap") -> str:
        if not self.memory_fabric:
            return json.dumps({"status": "error", "message": "MemoryFabric not available"}, indent=2)
        try:
            res = self.memory_fabric.hydrate(agent_id=agent_id, query=query, mode=mode)
            return json.dumps(res.to_dict(), indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)}, indent=2)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {"name": name, "description": f"Unified MCP tool for {name}", "input_schema": {"type": "object"}}
            for name in self.tools.keys()
        ]

    def execute_tool(self, name: str, kwargs: Dict[str, Any]) -> str:
        if name not in self.tools:
            return json.dumps({"error": f"Unknown cloud MCP tool: {name}"})
        return self.tools[name](**kwargs)

if __name__ == "__main__":
    mcp = UnifiedCloudMCPServer()
    print("=================================================================")
    print("  XORAS::OS - UNIFIED CLOUD & MEMORY MCP SERVER ACTIVE")
    print("=================================================================")
    print(f"[+] Active Unified MCP Tools ({len(mcp.list_tools())}): {[t['name'] for t in mcp.list_tools()]}")
    print("=================================================================")
