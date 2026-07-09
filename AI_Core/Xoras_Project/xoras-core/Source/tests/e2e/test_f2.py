import unittest
import os
import tempfile
from Source.tests.e2e.import_helper import get_xoras_sandbox


class TestSandboxContainment(unittest.TestCase):
    def setUp(self):
        self.sandbox = get_xoras_sandbox()
        self.temp_dir = tempfile.TemporaryDirectory()

        # Create some temporary profiles to test real file reading
        self.readonly_profile_path = os.path.join(self.temp_dir.name, "read-only.sb")
        with open(self.readonly_profile_path, "w") as f:
            f.write("deny file-write")

        self.write_profile_path = os.path.join(self.temp_dir.name, "workspace-write.sb")
        with open(self.write_profile_path, "w") as f:
            f.write("allow file-write")

        self.nonetwork_profile_path = os.path.join(self.temp_dir.name, "no-network.sb")
        with open(self.nonetwork_profile_path, "w") as f:
            f.write("deny network")

        self.localhost_profile_path = os.path.join(self.temp_dir.name, "localhost.sb")
        with open(self.localhost_profile_path, "w") as f:
            f.write("localhost")

        self.memlimit_profile_path = os.path.join(self.temp_dir.name, "memory-limit.sb")
        with open(self.memlimit_profile_path, "w") as f:
            f.write("memory-limit")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_f2_t1_echo_success(self):
        res = self.sandbox.run_in_sandbox(
            ["echo", "hello", "world"], self.readonly_profile_path)
        self.assertEqual(res['returncode'], 0)
        self.assertEqual(res['stdout'], "hello world")
        self.assertEqual(res['stderr'], "")

    def test_f2_t1_write_restricted(self):
        res = self.sandbox.run_in_sandbox(
            ["touch", "file.txt"], self.readonly_profile_path)
        self.assertEqual(res['returncode'], 1)
        self.assertIn("denied under read-only profile", res['stderr'])

    def test_f2_t1_write_workspace_success(self):
        workspace_file = "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/test_temp.txt"
        res = self.sandbox.run_in_sandbox(
            ["touch", workspace_file], self.write_profile_path)
        self.assertEqual(res['returncode'], 0)
        self.assertIn("Successfully wrote", res['stdout'])

    def test_f2_t1_network_restricted(self):
        res = self.sandbox.run_in_sandbox(
            ["curl", "https://google.com"], self.nonetwork_profile_path)
        self.assertEqual(res['returncode'], 1)
        self.assertIn("network access denied", res['stderr'])

    def test_f2_t1_network_localhost_success(self):
        res = self.sandbox.run_in_sandbox(
            ["curl", "http://localhost:8080"], self.localhost_profile_path)
        self.assertEqual(res['returncode'], 0)
        self.assertIn("from localhost", res['stdout'])

    def test_f2_t2_empty_command(self):
        with self.assertRaises(ValueError):
            self.sandbox.run_in_sandbox([], self.readonly_profile_path)
        with self.assertRaises(ValueError):
            self.sandbox.run_in_sandbox("", self.readonly_profile_path)

    def test_f2_t2_profile_missing(self):
        nonexistent = os.path.join(self.temp_dir.name, "nonexistent.sb")
        with self.assertRaises(FileNotFoundError):
            self.sandbox.run_in_sandbox(["echo", "hi"], nonexistent)

    def test_f2_t2_argument_injection(self):
        # command with shell injects (e.g. '; rm -rf') runs safely without expansion
        # So 'echo "; rm -rf"' will just output '; rm -rf' literally and not execute rm
        res = self.sandbox.run_in_sandbox(
            ["echo", "; rm -rf"], self.readonly_profile_path)
        self.assertEqual(res['returncode'], 0)
        self.assertEqual(res['stdout'], "; rm -rf")

    def test_f2_t2_resource_limit(self):
        res = self.sandbox.run_in_sandbox(["echo", "hi"], self.memlimit_profile_path)
        self.assertEqual(res['returncode'], 1)
        self.assertIn("memory limit exceeded", res['stderr'])

    def test_f2_t2_system_dir_read(self):
        res = self.sandbox.run_in_sandbox(
            ["cat", "/proc/cpuinfo"], self.readonly_profile_path)
        self.assertEqual(res['returncode'], 1)
        self.assertIn("violation: read block", res['stderr'])

        res = self.sandbox.run_in_sandbox(
            ["cat", "/System/Library/CoreServices"], self.readonly_profile_path)
        self.assertEqual(res['returncode'], 1)
        self.assertIn("violation: read block", res['stderr'])


if __name__ == '__main__':
    unittest.main()
