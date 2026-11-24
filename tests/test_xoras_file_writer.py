#!/usr/bin/env python3
"""
Adversarial acceptance tests for the sovereign file writer
==========================================================

These tests exist to break the writer, not to flatter it. Each one names the
defect it guards against. If any fails, the writer must not be installed.

Run: ``.venv/bin/python -m pytest tests/test_xoras_file_writer.py -q``
"""

from __future__ import annotations

import json
import os
import pathlib
import stat
import sys
import threading

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "core" / "ops" / "tools"))

import xoras_file_writer as writer_mod  # noqa: E402
from xoras_file_writer import (  # noqa: E402
    FileWriterError,
    SovereignFileWriter,
    SovereigntyViolation,
)


@pytest.fixture()
def w(tmp_path):
    return SovereignFileWriter(agent_id="TEST_SEAT", root=tmp_path / "writer")


# --- containment: defect 2 ------------------------------------------------
@pytest.mark.parametrize(
    "bad_name",
    ["../escape.txt", "../../etc/passwd", "/etc/passwd", "~/x.txt", "a/../../b.txt"],
)
def test_filename_cannot_escape_staging(w, bad_name):
    with pytest.raises(SovereigntyViolation):
        w.stage_file(bad_name, "payload")


@pytest.mark.parametrize("bad_sub", ["..", "../..", "/tmp", "a/../../b"])
def test_subfolder_cannot_escape_staging(w, bad_sub):
    with pytest.raises(SovereigntyViolation):
        w.stage_file("ok.txt", "payload", subfolder=bad_sub)


def test_absolute_desired_filename_is_refused(w):
    staged = w.stage_file("ok.txt", "payload")
    with pytest.raises(SovereigntyViolation):
        w.publish_artifact(staged, desired_filename="/tmp/outside.txt")


def test_publish_refuses_file_outside_staging(w, tmp_path):
    outside = tmp_path / "outside.txt"
    outside.write_text("not staged")
    with pytest.raises(SovereigntyViolation):
        w.publish_artifact(outside)


# --- symlinks: defect 3 ---------------------------------------------------
def test_symlinked_target_file_is_refused(w):
    target = w.staging_dir / "work" / "link.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    outside = w.root / "outside.txt"
    outside.write_text("outside")
    target.symlink_to(outside)
    with pytest.raises(SovereigntyViolation):
        w.stage_file("link.txt", "payload")
    assert outside.read_text() == "outside"


def test_symlinked_subfolder_is_refused(w):
    outside_dir = w.root / "outside_dir"
    outside_dir.mkdir()
    (w.staging_dir / "evil").symlink_to(outside_dir, target_is_directory=True)
    with pytest.raises(SovereigntyViolation):
        w.stage_file("x.txt", "payload", subfolder="evil")
    assert not (outside_dir / "x.txt").exists()


def test_publish_refuses_symlinked_staged_file(w):
    real = w.stage_file("real.txt", "payload")
    alias = w.staging_dir / "work" / "alias.txt"
    alias.symlink_to(real)
    with pytest.raises(SovereigntyViolation):
        w.publish_artifact(alias)


# --- policy and syntax: defect 6 -----------------------------------------
def test_html_refused_by_default(w):
    with pytest.raises(FileWriterError) as exc:
        w.stage_file("page.html", "<html></html>")
    assert "POLICY REJECTION" in str(exc.value)


def test_html_override_is_allowed_and_recorded(w):
    w.stage_file("page.html", "<html></html>", allow_html=True)
    record = json.loads(w.audit_file.read_text().splitlines()[-1])
    assert record["policy_override"] == "html"


def test_invalid_python_refused(w):
    with pytest.raises(FileWriterError) as exc:
        w.stage_file("bad.py", "def broken(:")
    assert "SYNTAX REJECTION" in str(exc.value)


def test_invalid_json_refused(w):
    with pytest.raises(FileWriterError):
        w.stage_file("bad.json", "{nope}")


def test_utf8_decode_failure_refused_for_text_extensions(w):
    with pytest.raises(FileWriterError):
        w.stage_file("bad.py", b"\xff\xfe\x00def x():\n")


def test_publish_revalidates_tampered_staged_python(w):
    """The v2.0 defect: publish read bytes and skipped the AST gate."""
    staged = w.stage_file("good.py", "x = 1\n")
    staged.write_text("def broken(:\n")
    with pytest.raises(FileWriterError) as exc:
        w.publish_artifact(staged)
    assert "SYNTAX REJECTION" in str(exc.value)


# --- atomicity and concurrency: defects 4 and 5 --------------------------
def test_concurrent_writers_never_interleave(w):
    payloads = [f"{i}:" + "x" * 4000 + "\n" for i in range(8)]
    errors: list[BaseException] = []

    def worker(payload: str) -> None:
        try:
            for _ in range(4):
                w.stage_file("contended.txt", payload)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(p,)) for p in payloads]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, errors
    final = (w.staging_dir / "work" / "contended.txt").read_text()
    assert final in payloads, "final file is a mix of writers, not one payload"


def test_publish_is_atomic_and_leaves_no_temp_files(w):
    staged = w.stage_file("doc.md", "# doc\n" * 100)
    w.publish_artifact(staged)
    leftovers = [p.name for p in w.publish_dir.iterdir() if p.name.endswith(".tmp")]
    assert leftovers == []


# --- versioning: defect 7 ------------------------------------------------
def test_versioning_counts_the_publish_directory(w):
    names = [w.write_and_publish("report.md", f"body {i}\n")[0] for i in range(3)]
    assert names == ["report.md", "report-v2.md", "report-v3.md"]
    assert sorted(p.name for p in w.publish_dir.iterdir()) == sorted(names)


def test_republishing_different_content_never_overwrites(w):
    w.write_and_publish("a.txt", "first\n")
    w.write_and_publish("a.txt", "second\n")
    assert (w.publish_dir / "a.txt").read_text() == "first\n"
    assert (w.publish_dir / "a-v2.txt").read_text() == "second\n"


# --- audit: defect 8 -----------------------------------------------------
def test_audit_chain_links_every_record(w):
    w.write_and_publish("one.txt", "1\n")
    w.write_and_publish("two.txt", "2\n")
    records = [json.loads(line) for line in w.audit_file.read_text().splitlines()]
    assert records[0]["prev"] == "GENESIS"
    for previous, current in zip(records, records[1:]):
        assert current["prev"] == previous["record_sha256"]
    ok, line, _ = w.verify_audit()
    assert ok and line is None


def test_audit_tamper_is_detected(w):
    w.write_and_publish("one.txt", "1\n")
    lines = w.audit_file.read_text().splitlines()
    record = json.loads(lines[0])
    record["bytes_written"] = 999
    lines[0] = json.dumps(record, sort_keys=True)
    w.audit_file.write_text("\n".join(lines) + "\n")
    ok, line, _ = w.verify_audit()
    assert not ok and line == 1


def test_audit_failure_removes_the_unreceipted_artifact(w, monkeypatch):
    def boom(_record):
        raise OSError("ledger unavailable")

    monkeypatch.setattr(w, "_append_receipt", boom)
    with pytest.raises(OSError):
        w.write_and_publish("orphan.txt", "payload\n")
    assert not (w.publish_dir / "orphan.txt").exists(), "artifact exists without a receipt"
    assert not (w.staging_dir / "publish_staging" / "orphan.txt").exists()


def test_corrupt_audit_refuses_further_appends(w):
    w.stage_file("first.txt", "1\n")
    w.audit_file.write_text("{not json}\n")
    with pytest.raises(FileWriterError):
        w.stage_file("second.txt", "2\n")


# --- bounds --------------------------------------------------------------
def test_size_cap_on_stage(w):
    small = SovereignFileWriter(agent_id="TEST_SEAT", root=w.root, max_bytes=32)
    with pytest.raises(FileWriterError):
        small.stage_file("big.txt", "x" * 33)


def test_size_cap_on_publish(w, tmp_path):
    # Disk-independent: prove the SIZE-CAP BRANCH with a small bound instead of
    # allocating 64MB+1 on disk (which Errno 28 on a full volume, masking the
    # guard under test). The production default (64MB) is unchanged; only this
    # test's writer uses a tiny cap. The guard logic is identical at any bound.
    small = SovereignFileWriter(agent_id="TEST_SEAT", root=tmp_path / "cap",
                                max_bytes=64)
    staged = small.stage_file("big.txt", "x" * 8)
    staged.write_bytes(b"x" * (small.max_bytes + 1))
    with pytest.raises(FileWriterError):
        small.publish_artifact(staged)


def test_empty_and_whitespace_content_refused(w):
    with pytest.raises(FileWriterError):
        w.stage_file("empty.txt", b"")
    with pytest.raises(FileWriterError):
        w.stage_file("blank.txt", "   \n\t\n")


def test_control_characters_in_filename_refused(w):
    with pytest.raises(FileWriterError):
        w.stage_file("bad\x00name.txt", "x")


@pytest.mark.parametrize("bad_agent", ["", "a b", "x;rm -rf /", "AGENT/../x"])
def test_invalid_agent_id_refused(tmp_path, bad_agent):
    with pytest.raises(FileWriterError):
        SovereignFileWriter(agent_id=bad_agent, root=tmp_path / "w")


# --- permissions ---------------------------------------------------------
def test_created_files_are_owner_only(w):
    staged = w.stage_file("private.txt", "secret\n")
    mode = stat.S_IMODE(staged.stat().st_mode)
    assert mode == 0o600, oct(mode)


# --- falsification of the old v2 self-test ------------------------------
def test_self_test_returns_zero_and_asserts():
    assert writer_mod.self_test() == 0


# --- RAW post-write verification (added hardening) ------------------------
def test_post_write_hash_mismatch_is_rejected(w):
    """A silent write that lands different bytes must never get a clean receipt."""

    class CorruptingWriter(SovereignFileWriter):
        def _atomic_write(self, directory, name, payload):
            return super()._atomic_write(directory, name, payload + b"CORRUPT")

    broken = CorruptingWriter(agent_id="TEST_SEAT", root=w.root)
    with pytest.raises(FileWriterError, match="RAW REJECTION"):
        broken.stage_file("silent.txt", "payload")
    assert not (w.staging_dir / "work" / "silent.txt").exists()


def test_publish_verifies_bytes_on_disk(w):
    staged = w.stage_file("raw.txt", "payload")

    class CorruptingWriter(SovereignFileWriter):
        def _atomic_write(self, directory, name, payload):
            return super()._atomic_write(directory, name, payload + b"BAD")

    broken = CorruptingWriter(agent_id="TEST_SEAT", root=w.root)
    with pytest.raises(FileWriterError, match="RAW REJECTION"):
        broken.publish_artifact(staged)


# --- policy across every suffix and Unicode normalization ----------------
@pytest.mark.parametrize("bad_name", [
    "PAGE.HTML", "script.py.html", "payload.html.txt", "page．html", "x.htm.txt",
])
def test_html_policy_checks_every_suffix_and_nfkc(w, bad_name):
    with pytest.raises(FileWriterError):
        w.stage_file(bad_name, "<html></html>")
