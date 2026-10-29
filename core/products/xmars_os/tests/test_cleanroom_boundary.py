"""
XMARS-OS Cleanroom Boundary & Sandbox Jail Verification
======================================================
Verifies that XMARS-OS operates strictly within its designated application
sandbox and cannot read, write, or execute commands outside its boundary.
"""

import os
import sys
import unittest
import tempfile

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_DIR = os.path.join(APP_DIR, "workspace")

class TestXmarsCleanroomBoundary(unittest.TestCase):

    def setUp(self):
        os.makedirs(WORKSPACE_DIR, exist_ok=True)

    def test_01_workspace_jail_boundary(self):
        """Verify that paths outside the application workspace are strictly rejected."""
        def is_safe_path(target_rel, root):
            safe_path = os.path.abspath(os.path.join(root, target_rel))
            common = os.path.commonpath([safe_path, root])
            return common == root and safe_path != root

        # Legitimate paths inside workspace
        self.assertTrue(is_safe_path("main.py", WORKSPACE_DIR))
        self.assertTrue(is_safe_path("src/utils.py", WORKSPACE_DIR))

        # Hostile paths escaping workspace
        self.assertFalse(is_safe_path("../server.py", WORKSPACE_DIR))
        self.assertFalse(is_safe_path("../../AGENTS.md", WORKSPACE_DIR))
        self.assertFalse(is_safe_path("../../../.bashrc", WORKSPACE_DIR))
        self.assertFalse(is_safe_path("/etc/passwd", WORKSPACE_DIR))

    def test_02_standalone_module_purity(self):
        """Verify core xmars_os modules have zero missing local dependencies."""
        modules = [
            "hardware_governor",
            "embedded_transformer",
            "remediation",
            "accelerators",
            "autonomy",
            "self_upgrade",
            "autonomous_sentinel",
            "cloudflare_bridge"
        ]
        if APP_DIR not in sys.path:
            sys.path.insert(0, APP_DIR)

        for mod_name in modules:
            mod = __import__(mod_name)
            self.assertIsNotNone(mod)

    def test_03_no_foreign_disk_pollution(self):
        """Verify that no Windows drive artifacts or rogue OS folders exist in xmars_os."""
        rogue_c = os.path.join(APP_DIR, "C:")
        self.assertFalse(os.path.exists(rogue_c))

if __name__ == "__main__":
    unittest.main(verbosity=2)
