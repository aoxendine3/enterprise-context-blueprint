#!/usr/bin/env python3
"""
===============================================================================
XORAS::OS - PLATFORM DEPLOYMENT SUITE (LANE 1, 2, 3 GAUNTLET)
===============================================================================
Verifies Web (Bolt/v0), Mobile (Expo/Firebase), Desktop (Tauri/GitHub Actions),
and Platform MCP tool execution.
Author: The Lead 9 Council (Maxx, Clara, Vance, John, DAXX)
===============================================================================
"""

import os
import sys
import json
import time
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_deployer import SovereignWebDeployer
from mobile_deployer import SovereignMobileDeployer
from desktop_deployer import SovereignDesktopDeployer
from platform_mcp_server import SovereignPlatformMCPServer

class TestSovereignPlatformDeployment(unittest.TestCase):
    def setUp(self):
        self.web = SovereignWebDeployer()
        self.mobile = SovereignMobileDeployer()
        self.desktop = SovereignDesktopDeployer()
        self.mcp = SovereignPlatformMCPServer()

    def test_01_web_scaffold_bolt(self):
        res = self.web.scaffold_bolt_react_app("test_bolt_app", [{"name": "Header"}])
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["app_name"], "test_bolt_app")

    def test_02_web_deploy_v0_vercel(self):
        res = self.web.deploy_v0_vercel_app("test_v0_app")
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["deployment_url"].endswith(".vercel.app"))

    def test_03_mobile_scaffold_expo(self):
        res = self.mobile.scaffold_expo_app("test_expo_app")
        self.assertEqual(res["status"], "success")
        self.assertTrue(os.path.exists(os.path.join(res["app_path"], "app.json")))

    def test_04_mobile_firebase_spark(self):
        res = self.mobile.configure_firebase_spark_backend("test_expo_app")
        self.assertEqual(res["status"], "success")
        self.assertFalse(res["card_required"])

    def test_05_desktop_scaffold_tauri(self):
        res = self.desktop.scaffold_tauri_app("test_tauri_app")
        self.assertEqual(res["status"], "success")
        self.assertTrue(os.path.exists(os.path.join(res["app_path"], "src-tauri", "tauri.conf.json")))

    def test_06_desktop_github_actions_workflow(self):
        res = self.desktop.generate_github_actions_workflow("test_tauri_app")
        self.assertEqual(res["status"], "success")
        self.assertTrue(os.path.exists(res["workflow_path"]))

    def test_07_platform_mcp_tools(self):
        tools = self.mcp.list_tools()
        tool_names = [t["name"] for t in tools]
        self.assertIn("web_scaffold_bolt_react", tool_names)
        self.assertIn("mobile_scaffold_expo_app", tool_names)
        self.assertIn("desktop_scaffold_tauri_app", tool_names)

        out = json.loads(self.mcp.execute_tool("desktop_scaffold_tauri_app", {"app_name": "mcp_tauri_app"}))
        self.assertEqual(out["status"], "success")

if __name__ == "__main__":
    unittest.main(verbosity=2)
