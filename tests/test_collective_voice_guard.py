#!/usr/bin/env python3
"""
Automated Test: Collective Voice & Identity Scope Enforcement
Standard: AGENTS.md Section 10 (Collective Voice & Narration Cadence — ABSOLUTE RULE)
Proves the collective voice is mechanically enforceable, and that identity scope
(read / seal / branding / read-only) is wired into the wake path.
"""
import json
import os
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.ops.scripts.collective_voice_guard import check, PHASES


def test_collective_first_person_plural_accepted():
    assert check("We are pushing the ramp to the break point now.")["ok"] is True
    assert check("Our task is the verification gate.")["ok"] is True


def test_outside_first_person_singular_refused():
    for text in ("I will run the gauntlet.", "My task is the gate.", "Give me the receipt."):
        assert check(text)["ok"] is False, text


def test_outside_assistant_voice_refused():
    for text in ("As an AI assistant, I decline.", "The language model cannot answer.", "AI Assistant ready."):
        assert check(text)["ok"] is False, text


def test_foreign_product_branding_refused():
    for text in ("Antigravity rewrote the files.", "ChatGPT wrote this.", "GitHub Copilot suggests this."):
        assert check(text)["ok"] is False, text


def test_narration_phases_recognized():
    for phase in PHASES:
        res = check(f"[{phase}] We continue on the bench.")
        assert res["ok"] is True
        assert res["phase"] == phase


def test_quoted_code_artifacts_are_not_voice():
    assert check("```\nif (x) { return my_value; }\n```\nWe continue.")["ok"] is True


def test_agent_speak_enforces_voice_guard():
    speak = ROOT / "ops" / "scripts" / "agent_speak.sh"
    assert speak.exists()
    body = speak.read_text(encoding="utf-8")
    assert "collective_voice_guard.py" in body, "agent_speak.sh is not wired to the collective voice guard"
    assert "exit 5" in body, "agent_speak.sh must fail closed (exit 5) on a voice violation"


def test_turn_narration_contract_is_enforced():
    """Every turn must declare its phase, what it did, and what is next."""
    from core.ops.scripts.collective_voice_guard import check as guard_check

    # A compliant turn: phase + next stated.
    ok = guard_check("[NEXT] We are pushing the ramp now. Next we open the Windows plane.", require_plan=True)
    assert ok["ok"] is True, ok

    # Missing the phase marker entirely.
    assert guard_check("We are pushing the ramp now and next we open the Windows plane.",
                       require_plan=True)["ok"] is False

    # Phase present but nothing about what happens next.
    assert guard_check("[NEXT] We are pushing the ramp.", require_plan=True)["ok"] is False

    # Breakdown without a completed-work statement.
    assert guard_check("[BREAKDOWN] The ramp is running and the numbers look good.",
                       require_plan=True)["ok"] is False

    # A full breakdown: phase + done + next.
    full = guard_check(
        "[BREAKDOWN] We repaired the lineage migration and the suite is green now. "
        "Next we wire the identity guard into the wake contract.", require_plan=True)
    assert full["ok"] is True, full
    assert full["phase"] == "BREAKDOWN"


def test_turn_ledger_records_and_reports_intent():
    """The operator can always ask what an agent is doing."""
    import tempfile
    from core.ops.scripts import turn_ledger

    original = turn_ledger.LEDGER
    with tempfile.TemporaryDirectory() as td:
        turn_ledger.LEDGER = Path(td) / "turn_ledger.jsonl"
        try:
            turn_ledger.record("maxx", "NEXT", "We are auditing the estate now. Next we bring the digest.")
            turn_ledger.record("maxx", "BREAKDOWN", "We completed the deep digest and it is green now. Next we repair what it found.")
            state = turn_ledger.status("maxx")
            assert state["maxx"]["turns"] == 2
            assert "digest" in state["maxx"]["last_done"].lower()
            assert state["maxx"]["doing_next"]
        finally:
            turn_ledger.LEDGER = original


def test_identity_scope_guard_is_wired_into_wake():
    wake = ROOT / "ops" / "scripts" / "wake_contract.sh"
    assert wake.exists()
    body = wake.read_text(encoding="utf-8")
    assert "identity_scope_guard.py" in body, "wake contract stage 1 must scope identity, not print it"


def test_citizen_cards_are_sealed_and_read_only():
    guard = ROOT / "core" / "ops" / "security" / "identity_scope_guard.py"
    assert guard.exists()
    manifest_path = ROOT / "identity" / "agent_card_manifest.json"
    assert manifest_path.exists(), "agent cards must be sealed"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest.get("cards"), "seal pins no cards"
    maxx = ROOT / "Xoras_agent_cards" / "maxx.json"
    assert maxx.exists(), "Maxx citizen card must be present in the active surface"
    mode = maxx.stat().st_mode
    assert not (mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)), "agent cards must be write-protected"
