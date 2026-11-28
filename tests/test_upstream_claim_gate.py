#!/usr/bin/env python3
"""Tests for core/ops/discernment/upstream_claim_gate.py."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
TMP_ROOT = ROOT / "tmp"
TMP_ROOT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "core" / "ops" / "discernment"))
import upstream_claim_gate as ucg  # noqa: E402


class UpstreamClaimGateTests(unittest.TestCase):
    def setUp(self):
        self.spans = ucg.index_spans([
            ("GQS-020:context", "The Trinity Gate enforces a 2-out-of-3 BFT quorum across Maxx, Clara, and Vance."),
            ("GQS-020:truth", "2-out-of-3 Byzantine quorum with bounded timeout escalation and dead-man switch detection."),
        ])

    def test_valid_grounded_claim_is_promoted(self):
        raw = {
            "abstain": False,
            "reason": "supported",
            "claims": [{
                "claim": "The Trinity Gate enforces a 2-out-of-3 BFT quorum across Maxx, Clara, and Vance.",
                "span_id": "SPAN-01",
                "quote": "The Trinity Gate enforces a 2-out-of-3 BFT quorum across Maxx, Clara, and Vance.",
            }],
        }
        v = ucg.validate_structured_response(raw, self.spans)
        self.assertEqual(v["status"], "PROMOTED_GROUNDED")
        self.assertFalse(v["abstained"])
        self.assertEqual(len(v["promoted_claims"]), 1)
        self.assertEqual(v["taint"], "0xBEAF0000")

    def test_spoofed_span_misquote_and_fake_symbol_are_blocked_upstream(self):
        raw = {
            "abstain": False,
            "reason": "guessing",
            "claims": [
                {"claim": "Fake claim", "span_id": "SPAN-99", "quote": "Fake"},
                {"claim": "Misquoted claim", "span_id": "SPAN-01", "quote": "Waits indefinitely for stalled agent"},
                {
                    "claim": "Calls fabricated_nonexistent_bypass_xyz() on quorum.",
                    "span_id": "SPAN-01",
                    "quote": "The Trinity Gate enforces a 2-out-of-3 BFT quorum across Maxx, Clara, and Vance.",
                },
            ],
        }
        v = ucg.validate_structured_response(raw, self.spans)
        self.assertTrue(v["abstained"])
        self.assertEqual(v["status"], "ABSTAIN_ALL_CLAIMS_REJECTED")
        self.assertEqual(len(v["promoted_claims"]), 0)
        self.assertEqual(len(v["rejected_claims"]), 3)
        self.assertEqual(v["emitted_text"], "ABSTAIN: INSUFFICIENT_EVIDENCE")

    def test_empty_spans_forces_abstention(self):
        raw = {"abstain": False, "reason": "confident guess", "claims": [{"claim": "x", "span_id": "SPAN-01", "quote": "x"}]}
        v = ucg.validate_structured_response(raw, {})
        self.assertTrue(v["abstained"])
        self.assertEqual(v["status"], "ABSTAIN_INSUFFICIENT_EVIDENCE")

    @patch("urllib.request.urlopen")
    def test_constrained_ollama_query_and_receipt_logging(self, mock_open):
        m = MagicMock()
        m.read.return_value = json.dumps({
            "response": json.dumps({
                "abstain": True,
                "reason": "insufficient evidence for unanswerable query",
                "claims": [],
            })
        }).encode("utf-8")
        m.__enter__ = lambda s: s
        m.__exit__ = lambda s, *a: False
        mock_open.return_value = m

        with tempfile.TemporaryDirectory(dir=str(TMP_ROOT)) as td:
            orig = ucg.RECEIPT_LOG
            ucg.RECEIPT_LOG = Path(td) / "ucg.jsonl"
            try:
                v = ucg.query_ollama_constrained("What is the secret quantum key?", self.spans)
                self.assertTrue(v["abstained"])
                self.assertEqual(v["status"], "ABSTAIN_INSUFFICIENT_EVIDENCE")
                self.assertTrue(ucg.RECEIPT_LOG.is_file())
            finally:
                ucg.RECEIPT_LOG = orig


if __name__ == "__main__":
    unittest.main()
