#!/usr/bin/env python3
"""Tests for core/ops/scripts/retain_recall.py (lossless distillation, CAS, recall)."""
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "core" / "ops" / "scripts"))
import retain_recall as rr  # noqa: E402


def _db(path: Path) -> Path:
    c = sqlite3.connect(path)
    c.execute("CREATE TABLE task_checkpoints (task_id TEXT, step_completed TEXT, total_steps TEXT, "
              "payload_json TEXT, status TEXT, updated_at TEXT, recovery_sig TEXT)")
    c.commit()
    c.close()
    return path


class RetainRecallTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.dir = Path(self.td.name)
        self.j = self.dir / "ko.jsonl"
        self.db = _db(self.dir / "w.db")

    def tearDown(self):
        self.td.cleanup()

    def _session(self):
        art = self.dir / "a.txt"
        art.write_text("proof")
        return {"session_id": "s1", "decisions": [
            {"decision": "Lock ROOTS", "reason": "no self mutation", "tags": ["Identity"], "artifact": str(art)},
            {"decision": "Seal AGENTS", "reason": "tamper evidence", "tags": ["seal"]},
            {"decision": "", "reason": "missing decision"},
        ]}

    def test_distill_retains_dedupes_and_surfaces_rejects(self):
        r1 = rr.distill(self._session(), "maxx", self.j)
        self.assertEqual(len(r1["retained"]), 2)
        self.assertEqual(len(r1["rejected"]), 1)
        r2 = rr.distill(self._session(), "maxx", self.j)
        self.assertEqual(r2["retained"], [])
        self.assertEqual(len(r2["duplicates"]), 2)
        recs = rr.read_journal(self.j)
        self.assertEqual(len(recs), 2)
        self.assertIsNotNone(recs[0]["artifact_sha256"])
        self.assertIsNone(recs[1]["artifact_sha256"])

    def test_chain_detects_edit_and_deletion(self):
        rr.distill(self._session(), "maxx", self.j)
        self.assertTrue(rr.verify_chain(self.j)[0])
        lines = self.j.read_text().splitlines()
        self.j.write_text(lines[1] + "\n")  # drop first record
        self.assertIn("prev_hash", rr.verify_chain(self.j)[1])
        self.j.write_text(lines[0].replace("Lock ROOTS", "Unlock ROOTS") + "\n" + lines[1] + "\n")
        self.assertIn("edited", rr.verify_chain(self.j)[1])

    def test_empty_journal_is_valid(self):
        self.assertTrue(rr.verify_chain(self.j)[0])
        self.assertEqual(rr.read_journal(self.j), [])

    def test_recall_ranks_and_handles_empty_query(self):
        rr.distill(self._session(), "maxx", self.j)
        hits = rr.recall("identity lock", journal=self.j)
        self.assertEqual(hits[0]["decision"], "Lock ROOTS")
        self.assertEqual(rr.recall("", journal=self.j), [])
        self.assertEqual(rr.recall("zzzz", journal=self.j), [])

    def test_checkpoint_cas_chain(self):
        a = rr.checkpoint("T", 1, 3, "running", {"k": 1}, self.db)
        b = rr.checkpoint("T", 2, 3, "running", {}, self.db)
        self.assertTrue(a["ok"] and b["ok"])
        self.assertNotEqual(a["recovery_sig"], b["recovery_sig"])
        bad = rr.checkpoint("T", 0, 3, "running", {}, self.db)
        self.assertFalse(bad["ok"])
        self.assertIn("CAS_REJECT", bad["reason"])
        rows = rr.latest_checkpoints(10, self.db)
        self.assertEqual(len(rows), 2)  # history preserved, regression not written

    def test_latest_checkpoints_missing_db(self):
        self.assertEqual(rr.latest_checkpoints(5, self.dir / "none.db"), [])

    def test_hydrate_reports_state(self):
        rr.distill(self._session(), "maxx", self.j)
        rr.checkpoint("T", 1, 3, "running", {}, self.db)
        h = rr.hydrate(5, self.j, self.db)
        self.assertTrue(h["chain_ok"])
        self.assertEqual(h["knowledge_objects_total"], 2)
        self.assertEqual(len(h["checkpoints"]), 1)

    def test_self_test_passes(self):
        self.assertEqual(rr.self_test(), 0)

    def test_retract_hides_but_preserves(self):
        ids = rr.distill(self._session(), "maxx", self.j)["retained"]
        self.assertFalse(rr.retract(["KO-nope"], "x", "maxx", self.j)["ok"])
        self.assertFalse(rr.retract(ids[:1], "  ", "maxx", self.j)["ok"])
        res = rr.retract(ids[:1], "test noise", "maxx", self.j)
        self.assertTrue(res["ok"])
        self.assertEqual(len(rr.read_journal(self.j)), 3)  # nothing deleted
        self.assertTrue(rr.verify_chain(self.j)[0])
        self.assertEqual(len(rr.active_objects(self.j)), 1)
        self.assertEqual(rr.recall("lock roots", journal=self.j), [])
        h = rr.hydrate(5, self.j, self.db)
        self.assertEqual((h["knowledge_objects_total"], h["retracted"]), (1, 1))

    def test_defaults_resolve_at_call_time(self):
        """Regression: module-level paths must be honoured, never frozen at import."""
        orig = (rr.JOURNAL, rr.WORLD_DB)
        rr.JOURNAL, rr.WORLD_DB = self.j, self.db
        try:
            rr.distill(self._session(), "maxx")
            rr.checkpoint("D", 1, 1, "done", {})
            self.assertTrue(self.j.exists())
            self.assertEqual(len(rr.latest_checkpoints(5)), 1)
        finally:
            rr.JOURNAL, rr.WORLD_DB = orig

    def test_cli_paths(self):
        s = self.dir / "s.json"
        s.write_text(json.dumps(self._session()))
        orig = (rr.JOURNAL, rr.WORLD_DB)
        rr.JOURNAL, rr.WORLD_DB = self.j, self.db
        try:
            for argv in (["distill", "--author", "maxx", "--session", str(s)],
                         ["recall", "seal"],
                         ["checkpoint", "--task", "T", "--step", "1", "--total", "2"],
                         ["hydrate"], ["verify"]):
                sys.argv = ["retain_recall"] + argv
                self.assertEqual(rr.main(), 0, argv)
            kid = rr.active_objects()[0]["object_id"]
            sys.argv = ["retain_recall", "retract", "--author", "maxx", "--reason", "r", kid]
            self.assertEqual(rr.main(), 0)
            sys.argv = ["retain_recall", "retract", "--author", "maxx", "--reason", "r", "KO-nope"]
            self.assertEqual(rr.main(), 1)
            sys.argv = ["retain_recall", "--self-test"]
            self.assertEqual(rr.main(), 0)
            sys.argv = ["retain_recall"]
            self.assertEqual(rr.main(), 2)
            sys.argv = ["retain_recall", "checkpoint", "--task", "T", "--step", "0", "--total", "2"]
            self.assertEqual(rr.main(), 1)
        finally:
            rr.JOURNAL, rr.WORLD_DB = orig


if __name__ == "__main__":
    unittest.main()
