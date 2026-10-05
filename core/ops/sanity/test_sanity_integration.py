#!/usr/bin/env python3
"""
===============================================================================
XORAS::OS - SANITY INTEGRATION SUITE (MARS LAYER 4 GAUNTLET)
===============================================================================
Verifies Sanity Client, MCP Server, Sync Daemon, and GROQ Query Pipelines
under zero-network and live deployment modes.
Author: The Lead 9 Council (Maxx, Clara, Vance, John, DAXX)
===============================================================================
"""

import os
import sys
import json
import time
import unittest
from pathlib import Path

# Add current directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sanity_client import SovereignSanityClient
from sanity_mcp_server import SanityMCPServer
from sanity_sync_daemon import SovereignSanitySyncDaemon

class TestSovereignSanityIntegration(unittest.TestCase):
    def setUp(self):
        self.client = SovereignSanityClient()
        self.mcp = SanityMCPServer()
        self.daemon = SovereignSanitySyncDaemon()

    def test_01_token_resolution(self):
        self.assertIsNotNone(self.client.token, "Sanity API token must resolve from key store or env.")
        self.assertTrue(len(self.client.token) > 20, "Sanity token length must be > 20 chars.")

    def test_02_groq_execution(self):
        res = self.client.execute_groq_query('*[_type == "sovereign_document"]')
        self.assertIn(res["status"], ("success", "offline_airgap_mode"))
        self.assertIn("result", res)

    def test_03_document_mutation(self):
        res = self.client.create_document("unit_test_doc", {
            "title": "Sanity Integration Unit Test",
            "timestamp": time.time()
        }, doc_id="test_unit_001")
        self.assertIn(res["status"], ("success", "offline_airgap_mode"))
        self.assertIn("transaction_id", res)

    def test_04_release_staging(self):
        res = self.client.stage_content_release("Sprint_Zero", [
            {"create": {"_type": "release_doc", "title": "Staged Document"}}
        ])
        self.assertIn("release_id", res)
        self.assertTrue(res["release_id"].startswith("release_sprint_zero"))

    def test_05_mcp_server_tools(self):
        tools = self.mcp.list_tools()
        tool_names = [t["name"] for t in tools]
        self.assertIn("sanity_groq_query", tool_names)
        self.assertIn("sanity_create_document", tool_names)

        schema_out = json.loads(self.mcp.execute_tool("sanity_fetch_schema", {}))
        self.assertEqual(schema_out["version"], "1.0.0")

    def test_06_sync_daemon(self):
        v_count = self.daemon.sync_v_and_v_documents()
        g_count = self.daemon.sync_golden_datasets()
        self.assertGreaterEqual(v_count + g_count, 1)

if __name__ == "__main__":
    unittest.main(verbosity=2)
