#!/usr/bin/env python3
"""Adversarial fuzz & concurrency gauntlet for retain_recall and identity_scope_guard."""
import concurrent.futures
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TMP_ROOT = ROOT / "tmp"
TMP_ROOT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "core" / "ops" / "scripts"))
sys.path.insert(0, str(ROOT / "core" / "ops" / "security"))

import retain_recall as rr  # noqa: E402
import identity_scope_guard as isg  # noqa: E402


def _make_db(path: Path) -> Path:
    c = sqlite3.connect(path)
    c.execute(
        "CREATE TABLE task_checkpoints (task_id TEXT, step_completed TEXT, total_steps TEXT, "
        "payload_json TEXT, status TEXT, updated_at TEXT, recovery_sig TEXT)"
    )
    c.commit()
    c.close()
    return path


class RetainRecallFuzzTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory(dir=str(TMP_ROOT))
        self.dir = Path(self.td.name)
        self.j = self.dir / "ko.jsonl"
        self.db = _make_db(self.dir / "w.db")

    def tearDown(self):
        self.td.cleanup()

    def test_fuzz_control_chars_unicode_and_oversized_payloads(self):
        payloads = [
            {"decision": "a\x00b\u200bc", "reason": "null and zero-width", "tags": ["Fuzz\x00"]},
            {"decision": "x" * 50000, "reason": "oversized", "artifact": "../../etc/passwd"},
            {"decision": "   \t\n  ", "reason": "whitespace-only decision"},
            {"decision": "valid", "reason": ""},
            {"decision": "emoji-\U0001f6e1\ufe0f-ok", "reason": "unicode", "tags": ["unicode"]},
        ]
        res = rr.distill({"session_id": "fuzz-1", "decisions": payloads}, "maxx", self.j)
        self.assertEqual(len(res["retained"]), 3)
        self.assertEqual(len(res["rejected"]), 2)
        ok, _ = rr.verify_chain(self.j)
        self.assertTrue(ok)
        # Path-traversal / non-existent artifact must never hash a host file outside existence check
        recs = rr.read_journal(self.j)
        self.assertIsNone(recs[1]["artifact_sha256"])

    def test_fuzz_recall_queries_never_crash(self):
        rr.distill({"session_id": "s", "decisions": [{"decision": "alpha", "reason": "beta"}]}, "maxx", self.j)
        for q in ["", "   ", "\x00\x01\x02", ".*" * 100, "\u200b\u202e", "alpha"]:
            out = rr.recall(q, limit=5, journal=self.j)
            self.assertIsInstance(out, list)

    def test_fuzz_corrupted_jsonl_and_tampered_hash_fail_closed(self):
        rr.distill({"session_id": "s", "decisions": [{"decision": "d1", "reason": "r1"}]}, "maxx", self.j)
        # Append truncated/corrupt JSON line -> verify_chain must fail closed cleanly (no traceback)
        with open(self.j, "a", encoding="utf-8") as fh:
            fh.write("{corrupt_json\n")
        ok, detail = rr.verify_chain(self.j)
        self.assertFalse(ok)
        self.assertIn("corrupt JSONL", detail)

        # Valid JSON with forged prev_hash
        self.j.unlink()
        rr.distill({"session_id": "s", "decisions": [{"decision": "d1", "reason": "r1"}]}, "maxx", self.j)
        rec = json.loads(self.j.read_text(encoding="utf-8").splitlines()[0])
        rec["prev_hash"] = "f" * 64
        self.j.write_text(json.dumps(rec) + "\n", encoding="utf-8")
        ok, detail = rr.verify_chain(self.j)
        self.assertFalse(ok)
        self.assertIn("prev_hash", detail)

    def test_concurrent_distill_and_checkpoints_preserve_chain(self):
        def worker(i: int):
            s = {"session_id": f"w-{i}", "decisions": [{"decision": f"dec-{i}", "reason": f"why-{i}"}]}
            r = rr.distill(s, "maxx", self.j)
            cp = rr.checkpoint(f"task-{i}", 1, 1, "done", {"worker": i}, self.db)
            return len(r["retained"]) == 1 and cp["ok"]

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(worker, range(16)))
        self.assertTrue(all(results))
        ok, _ = rr.verify_chain(self.j)
        self.assertTrue(ok)
        self.assertEqual(len(rr.read_journal(self.j)), 16)

    def test_identity_scope_guard_fuzz_agent_ids_fail_closed(self):
        for bad in ["../ROOTS", "maxx\x00", "", "   ", "nonexistent_agent_xyz", "a/b/c"]:
            ok, res = isg.verify(bad)
            self.assertFalse(ok, f"expected fail-closed for {bad!r}")
            self.assertEqual(res["verdict"], "FAIL_CLOSED")


if __name__ == "__main__":
    unittest.main()
