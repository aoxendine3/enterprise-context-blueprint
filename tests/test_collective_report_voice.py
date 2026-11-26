#!/usr/bin/env python3
"""Team-report voice is Maxx's card voice; the card, its .md and the citizens manifest must agree."""
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("collective_kokoro", REPO / "core" / "ops" / "scripts" / "collective_kokoro.py")
ck = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ck)


class ReportVoiceTests(unittest.TestCase):
    def test_report_voice_is_maxx_original(self):
        self.assertEqual(ck.report_voice(), "bm_george")

    def test_card_md_and_manifest_agree(self):
        card = json.loads((REPO / "Xoras_agent_cards" / "maxx.json").read_text(encoding="utf-8"))
        md = (REPO / "Xoras_agent_cards" / "maxx.md").read_text(encoding="utf-8")
        md_voice = re.search(r"Kokoro Neural Voice:\*\*\s*`([^`]+)`", md).group(1)
        md_fallback = re.search(r"Fallback Voice[^:]*:\*\*\s*`([^`]+)`", md).group(1)
        manifest = json.loads((REPO / "identity" / "sovereign_citizens_manifest.json").read_text(encoding="utf-8"))
        entry = next(c for c in manifest["citizens"] if c["agent_id"] == "maxx") \
            if "citizens" in manifest else None
        self.assertEqual(card["kokoro_voice_id"], md_voice)
        self.assertEqual(card["mac_fallback_voice"], md_fallback)
        if entry is not None:
            self.assertEqual(entry["kokoro_voice_id"], card["kokoro_voice_id"])
            self.assertEqual(entry["mac_fallback_voice"], card["mac_fallback_voice"])

    def test_fallback_when_card_unreadable(self):
        orig = ck.ROOT
        with tempfile.TemporaryDirectory() as td:
            ck.ROOT = Path(td)  # no card here
            try:
                self.assertEqual(ck.report_voice(), ck.REPORT_VOICE_FALLBACK)
                (Path(td) / "Xoras_agent_cards").mkdir()
                (Path(td) / "Xoras_agent_cards" / "maxx.json").write_text("{}")
                self.assertEqual(ck.report_voice(), ck.REPORT_VOICE_FALLBACK)
            finally:
                ck.ROOT = orig

    def test_empty_text_refused(self):
        import sys
        old = sys.argv
        sys.argv = ["collective_kokoro", "   "]
        try:
            self.assertEqual(ck.main(), 2)
        finally:
            sys.argv = old


if __name__ == "__main__":
    unittest.main()
