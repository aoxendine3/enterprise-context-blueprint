#!/usr/bin/env python3
"""
Acceptance tests for the fail-closed Poincaré write gate
========================================================

These tests are the contract. If any of them fails, the governor is not
fail-closed and must not be treated as production-ready.

They cover:

- honest anchor acceptance and honest restatement,
- signed semantic poison refused on every path,
- same-timestamp supersede unable to overwrite the honest baseline,
- unauthorised and forged supersede claims refused,
- an authorised seat still unable to bypass the geometric gate,
- gate errors, unembeddable values and future timestamps refused,
- deterministic authoritative read,
- numerical parity with the existing canonical Poincaré manifold
  (``labs/workspaces/sovra_nexus/sovra_core/poincare_hypergraph.py``).

Run: ``.venv/bin/python -m pytest tests/test_governor_poincare_gate.py -q``
"""

from __future__ import annotations

import hashlib
import math
import pathlib
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "core" / "ops" / "memory"))

import governed_memory_consolidation_engine as engine  # noqa: E402
import poincare_semantic_gate as gate_mod  # noqa: E402

TRUE_MASS = "18432.0"
POISON = "666.666"
KEY = "canonical_mass"


@pytest.fixture()
def harness(tmp_path, monkeypatch):
    monkeypatch.setattr(engine, "GOVERNANCE_DB", tmp_path / "governed_memory.db")
    monkeypatch.setattr(engine, "GOVERNANCE_JSONL", tmp_path / "receipts.jsonl")
    monkeypatch.setattr(engine, "GOVERNANCE_LOG", tmp_path / "gauntlet.log")

    source = tmp_path / "signed_telemetry_source.json"
    source.write_text('{"sensor": "cfd", "verified_mass": 18432.0}')
    merkle = hashlib.sha256(source.read_bytes()).hexdigest()

    gov = engine.GovernedMemoryGovernor()
    now = datetime.now(timezone.utc).replace(microsecond=0)

    def write(
        value,
        *,
        agent="clara",
        key=KEY,
        supersede=False,
        when=None,
        capsule=None,
        source_path=None,
        merkle_hash=None,
    ):
        return gov.evaluate_write_candidate(
            agent_id=agent,
            key=key,
            value=value,
            source_path=str(source_path or source),
            merkle_hash=merkle_hash if merkle_hash is not None else merkle,
            timestamp_iso=(when or now).isoformat(),
            target_capsule=capsule or agent,
            explicit_supersede=supersede,
        )

    def rows(key=KEY):
        conn = sqlite3.connect(engine.GOVERNANCE_DB)
        try:
            return conn.execute(
                "SELECT value, status, created_at FROM memory_records "
                "WHERE key = ? ORDER BY rowid",
                (key,),
            ).fetchall()
        finally:
            conn.close()

    return {
        "gov": gov,
        "now": now,
        "write": write,
        "rows": rows,
        "source": source,
        "merkle": merkle,
        "tmp": tmp_path,
    }


# --- happy path -------------------------------------------------------------
def test_honest_anchor_accepted(harness):
    res = harness["write"](TRUE_MASS)
    assert res["accepted"] is True
    assert res["status"] == "ACCEPTED"
    assert res["poincare"]["decision"] == "ANCHOR"
    assert res["veto_reasons"] == []
    assert harness["rows"]() == [(TRUE_MASS, "ACCEPTED", harness["now"].isoformat())]


def test_honest_restatement_accepted(harness):
    harness["write"](TRUE_MASS)
    res = harness["write"](TRUE_MASS, when=harness["now"] + timedelta(minutes=1))
    assert res["accepted"] is True
    assert res["poincare"]["decision"] == "PASS"
    assert res["axes"]["Supersession"] == pytest.approx(0.95)


def test_numeric_refinement_within_bound_accepted(harness):
    harness["write"]("100")
    res = harness["write"]("150", when=harness["now"] + timedelta(minutes=1))
    assert res["accepted"] is True, res["veto_reasons"]
    assert res["poincare"]["distance"] == pytest.approx(math.log(1.5), rel=1e-6)


# --- the attack -------------------------------------------------------------
def test_unannounced_poison_vetoed_and_not_stored(harness):
    harness["write"](TRUE_MASS)
    res = harness["write"](POISON, when=harness["now"] + timedelta(minutes=1))
    assert res["accepted"] is False
    assert res["status"] == "HARD_VETOED_BY_GOVERNOR"
    assert res["poincare"]["decision"] == "VETO"
    assert any("SEMANTIC_DRIFT_GATE" in r for r in res["veto_reasons"])
    assert [r[0] for r in harness["rows"]()] == [TRUE_MASS]
    assert harness["gov"].latest_accepted(KEY)["value"] == TRUE_MASS


def test_repeated_poison_vetoed_every_time(harness):
    harness["write"](TRUE_MASS)
    for minute in range(1, 6):
        res = harness["write"](POISON, when=harness["now"] + timedelta(minutes=minute))
        assert res["accepted"] is False, f"poison accepted at minute {minute}"
    assert len(harness["rows"]()) == 1


def test_insider_supersede_cannot_bypass(harness):
    harness["write"](TRUE_MASS)
    res = harness["write"](POISON, supersede=True)
    assert res["accepted"] is False
    assert any("UNAUTHORIZED_SUPERSEDE" in r for r in res["veto_reasons"])
    assert any("SEMANTIC_DRIFT_GATE" in r for r in res["veto_reasons"])
    assert [r[0] for r in harness["rows"]()] == [TRUE_MASS]


def test_authorised_seat_still_cannot_bypass_gate(harness):
    harness["write"](TRUE_MASS)
    res = harness["write"](POISON, supersede=True, agent="maxx")
    # The supersession axis is satisfied (0.95) — the gate is what stops it.
    assert res["axes"]["Supersession"] == pytest.approx(0.95)
    assert res["accepted"] is False
    assert res["poincare"]["decision"] == "VETO"
    assert [r[0] for r in harness["rows"]()] == [TRUE_MASS]


def test_forged_supersede_without_anchor_vetoed(harness):
    res = harness["write"](POISON, supersede=True)
    assert res["accepted"] is False
    assert "FORGED_SUPERSEDE_NO_ANCHOR" in res["veto_reasons"]
    assert harness["rows"]() == []


def test_same_timestamp_does_not_overwrite_honest_row(harness):
    harness["write"](TRUE_MASS)
    harness["write"](POISON, when=harness["now"])
    rows = harness["rows"]()
    assert len(rows) == 1
    assert rows[0][0] == TRUE_MASS
    assert rows[0][1] == "ACCEPTED"


# --- fail-closed edges ------------------------------------------------------
def test_gate_exception_fails_closed(harness, monkeypatch):
    harness["write"](TRUE_MASS)

    def boom(*args, **kwargs):
        raise RuntimeError("gate unavailable")

    monkeypatch.setattr(gate_mod, "evaluate_transition", boom)
    res = harness["write"](POISON, when=harness["now"] + timedelta(minutes=1))
    assert res["accepted"] is False
    assert any("GATE_UNAVAILABLE" in r for r in res["veto_reasons"])


def test_unembeddable_value_vetoed(harness):
    harness["write"](TRUE_MASS)
    res = harness["write"](None)
    assert res["accepted"] is False
    assert res["poincare"]["decision"] == "VETO"
    assert "NULL_VALUE" in res["poincare"]["reason"]


def test_unembeddable_baseline_fails_closed(harness):
    # Insert a legacy baseline whose text normalises to nothing.
    conn = sqlite3.connect(engine.GOVERNANCE_DB)
    conn.execute(
        "INSERT INTO memory_records (id, agent_id, key, value, status, created_at) "
        "VALUES ('legacy', 'clara', ?, '!!!', 'ACCEPTED', ?)",
        (KEY, harness["now"].isoformat()),
    )
    conn.commit()
    conn.close()

    res = harness["write"](TRUE_MASS, when=harness["now"] + timedelta(minutes=1))
    assert res["accepted"] is False
    assert "EMPTY_VALUE" in res["poincare"]["reason"]


def test_future_timestamp_vetoed(harness):
    res = harness["write"](TRUE_MASS, when=harness["now"] + timedelta(days=1))
    assert res["accepted"] is False
    assert any("STALE_PROPAGATION_RISK" in r for r in res["veto_reasons"])


def test_value_size_bound_enforced(harness):
    res = harness["write"]("X" * (engine.MAX_VALUE_CHARS + 1))
    assert res["accepted"] is False
    assert any("VALUE_TOO_LARGE" in r for r in res["veto_reasons"])


def test_text_cosmetic_equivalence_passes(harness):
    harness["write"]("port = 8080", key="service_port")
    res = harness["write"]("PORT=8080", key="service_port", when=harness["now"] + timedelta(minutes=1))
    assert res["accepted"] is True, res["veto_reasons"]
    assert res["poincare"]["distance"] == 0.0


def test_text_semantic_mutation_vetoed(harness):
    harness["write"]("port = 8080", key="service_port")
    res = harness["write"]("port = 9090", key="service_port", when=harness["now"] + timedelta(minutes=1))
    assert res["accepted"] is False
    assert "TEXT_VALUE_MUTATION" in res["poincare"]["reason"]


def test_numeric_beyond_bound_vetoed(harness):
    harness["write"]("100", key="load")
    res = harness["write"]("200", key="load", when=harness["now"] + timedelta(minutes=1))
    assert res["accepted"] is False
    assert res["poincare"]["decision"] == "VETO"


def test_latest_accepted_is_deterministic_with_tied_timestamps(harness):
    stamp = harness["now"].isoformat()
    conn = sqlite3.connect(engine.GOVERNANCE_DB)
    for value in ("first", "second"):
        conn.execute(
            "INSERT INTO memory_records (id, agent_id, key, value, status, created_at) "
            "VALUES (?, 'clara', 'tie_key', ?, 'ACCEPTED', ?)",
            (value, value, stamp),
        )
    conn.commit()
    conn.close()

    latest = harness["gov"].latest_accepted("tie_key")
    assert latest["value"] == "second"


# --- metric properties and parity with the existing manifold ----------------
def test_distance_identity_and_symmetry():
    for value in (0.0, 1.0, 0.5, -3.25, 18432.0):
        mode, u = gate_mod.embed_value(value)
        assert mode == "scalar"
        assert gate_mod.poincare_distance(u, u) == pytest.approx(0.0, abs=1e-12)
        _, v = gate_mod.embed_value(value * 1.5)
        assert gate_mod.poincare_distance(u, v) == pytest.approx(
            gate_mod.poincare_distance(v, u), rel=1e-12
        )


def test_scalar_distance_equals_log_ratio():
    for a, b in ((100.0, 150.0), (18432.0, 666.666), (0.5, 2.0), (-4.0, -10.0)):
        _, u = gate_mod.embed_value(a)
        _, v = gate_mod.embed_value(b)
        assert gate_mod.poincare_distance(u, v) == pytest.approx(
            abs(math.log(a / b)), rel=1e-9
        )


def test_sign_change_is_maximum_drift():
    result = gate_mod.evaluate_transition("18432.0", "-18432.0")
    assert result.decision == gate_mod.GateDecision.VETO
    assert result.reason == "SIGN_DISCONTINUITY"

    zero_crossing = gate_mod.evaluate_transition("0", "1")
    assert zero_crossing.decision == gate_mod.GateDecision.VETO
    assert zero_crossing.reason == "SIGN_DISCONTINUITY"


def test_parity_with_canonical_sovra_manifold():
    """
    The metric is not a new one. It is the canonical
    ``PoincareManifold.geodesic_distance`` from the existing sovra core.
    Parity is asserted on points inside that manifold's safe interior.
    """
    sovra = REPO / "labs" / "workspaces" / "sovra_nexus"
    if not (sovra / "sovra_core" / "poincare_hypergraph.py").exists():
        pytest.skip("canonical sovra_nexus manifold not present")

    sys.path.insert(0, str(sovra))
    try:
        from sovra_core.poincare_hypergraph import PoincareManifold
    finally:
        sys.path.pop(0)

    manifold = PoincareManifold(dim=4)
    u = [0.10, -0.20, 0.05, 0.30]
    v = [0.40, 0.10, -0.15, 0.20]
    assert gate_mod.poincare_distance(tuple(u), tuple(v)) == pytest.approx(
        manifold.geodesic_distance(u, v), rel=1e-12
    )
