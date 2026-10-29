"""
XMARS.os End-to-End Enterprise Gauntlet
========================================
Comprehensive verification covering:
1. All HTTP routes & visual assets (200 OK, valid content types)
2. Cleanroom workspace scoping (Strict isolation to xmars_os/workspace)
3. Jail security (Rejection of parent escapes, 404/403 fail-closed)
4. Model endpoint availability and governor context bounds (4096)
5. Interactive terminal execution scoped to sandboxed workspace
"""

import os
import sys
import unittest
import urllib.request
import urllib.error
import json

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
WORKSPACE_DIR = os.path.join(APP_DIR, "workspace")
BASE_URL = "http://127.0.0.1:8085"

class TestXmarsEndToEndGauntlet(unittest.TestCase):

    def test_01_all_web_routes_deliver_200_ok(self):
        """Verify all tabs, static assets, and APIs respond with 200 OK."""
        routes = [
            "/",
            "/landing",
            "/store",
            "/portal",
            "/connect",
            "/api/health",
            "/api/agents",
            "/api/models",
            "/api/tribrain",
            "/api/sentinel",
            "/api/upgrades",
            "/api/workspace/tree"
        ]
        for r in routes:
            url = f"{BASE_URL}{r}"
            try:
                res = urllib.request.urlopen(url, timeout=3)
                self.assertEqual(res.getcode(), 200, f"Route {r} returned {res.getcode()}")
                self.assertTrue(len(res.read()) > 0, f"Route {r} returned empty body")
            except Exception as e:
                self.fail(f"Route {r} failed with exception: {e}")

    def test_02_workspace_tree_isolation(self):
        """Verify the workspace tree returns only sandboxed items, not the parent brain."""
        res = urllib.request.urlopen(f"{BASE_URL}/api/workspace/tree", timeout=3)
        data = json.loads(res.read().decode())
        self.assertEqual(data.get("status"), "success")
        tree = data.get("tree", [])
        
        # Must contain workspace files
        file_names = [item["name"] for item in tree]
        self.assertIn("welcome.py", file_names)
        
        # Must NEVER contain parent repo folders like core, memory, or workspaces
        self.assertNotIn("core", file_names)
        self.assertNotIn("memory", file_names)
        self.assertNotIn("workspaces", file_names)
        self.assertNotIn(".git", file_names)

    def test_03_sandbox_read_and_hostile_jail_rejection(self):
        """Verify reading inside workspace succeeds and directory escape fails closed."""
        # Clean read
        r_ok = urllib.request.urlopen(f"{BASE_URL}/api/workspace/read?path=welcome.py", timeout=3)
        self.assertEqual(r_ok.getcode(), 200)
        body = json.loads(r_ok.read().decode())
        self.assertEqual(body.get("status"), "success")
        self.assertIn("Welcome to XMARS.os", body.get("content", ""))

        # Hostile escape attempt
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(f"{BASE_URL}/api/workspace/read?path=../../AGENTS.md", timeout=3)
        self.assertIn(ctx.exception.code, [403, 404])

    def test_04_hardware_governor_pinned_limits(self):
        """Verify that the hardware governor maintains context ceiling."""
        from hardware_governor import governor
        topo = governor.inspect_topology()
        self.assertEqual(topo["strict_context_window"], 4096)
        self.assertEqual(topo["pinned_kv_cache_limit_mb"], 512)

    def test_05_terminal_execution_isolation(self):
        """Verify terminal execution runs strictly inside the sandboxed workspace."""
        payload = json.dumps({"command": "pwd"}).encode("utf-8")
        req = urllib.request.Request(
            f"{BASE_URL}/api/terminal/exec",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        res = urllib.request.urlopen(req, timeout=5)
        self.assertEqual(res.getcode(), 200)
        out = json.loads(res.read().decode())
        self.assertEqual(out.get("exit_code"), 0)
        self.assertIn("workspace", out.get("stdout", ""))

if __name__ == "__main__":
    unittest.main(verbosity=2)
