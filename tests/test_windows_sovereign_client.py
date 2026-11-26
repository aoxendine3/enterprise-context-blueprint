#!/usr/bin/env python3
"""Unit tests for WindowsSovereignNodeClient: pins num_ctx=4096 to prevent 32K CPU stalls."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "core" / "ops" / "scripts"))
from windows_sovereign_client import WindowsSovereignNodeClient  # noqa: E402


class WindowsSovereignClientTests(unittest.TestCase):
    def _mock_resp(self, body: dict, status: int = 200):
        m = MagicMock()
        m.status = status
        m.read.return_value = json.dumps(body).encode("utf-8")
        m.__enter__ = lambda s: s
        m.__exit__ = lambda s, *a: False
        return m

    @patch("urllib.request.urlopen")
    def test_pin_and_query_enforce_pinned_num_ctx(self, mock_open):
        mock_open.side_effect = [
            self._mock_resp({"response": "ok"}),
            self._mock_resp({"response": "ready"}),
        ]
        c = WindowsSovereignNodeClient()
        self.assertTrue(c.pin_resident_model())
        res = c.query("ping", max_tokens=16)
        self.assertTrue(res["ok"])
        self.assertEqual(res["response"], "ready")
        for call in mock_open.call_args_list:
            req = call[0][0]
            payload = json.loads(req.data.decode("utf-8"))
            self.assertEqual(payload["options"]["num_ctx"], 4096)


if __name__ == "__main__":
    unittest.main()
