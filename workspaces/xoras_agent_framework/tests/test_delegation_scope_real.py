"""Real tests for scope-checked delegation (confused-deputy / privilege-escalation defense)."""

import pytest

from xoras.agents import AgentCard, AgentRoster
from xoras.council import (
    DEFAULT_MAX_DELEGATION_DEPTH,
    HIGH_IMPACT_SCOPES,
    CouncilOrchestrator,
    DelegationDenied,
)

SAFE = "def f(a: int) -> int:\n    return a + 1\n"


def card(aid, scopes=None, seat=1):
    return AgentCard(agent_id=aid, name=aid.upper(), role="r", seat=seat, status="ACTIVE", purpose="p", scopes=scopes)


@pytest.fixture
def orch():
    r = AgentRoster()
    r.register(card("low", ["fs:read", "net:fetch"]))
    r.register(card("mid", ["fs:read", "fs:write", "net:fetch"]))
    r.register(card("high", ["fs:read", "fs:write", "exec:shell", "secrets:read", "net:egress"]))
    r.register(card("legacy"))
    r.register(card("vance"))
    for i in range(8):
        r.register(card(f"n{i}", ["fs:read"]))
    return CouncilOrchestrator(roster=r)


def test_subset_allowed(orch):
    ctx = orch.begin_delegation("anthony", "mid", {"fs:read", "net:fetch"})
    child = orch.delegate(ctx, "low", {"fs:read"})
    assert child.effective_scopes == frozenset({"fs:read"})


def test_superset_denied(orch):
    ctx = orch.begin_delegation("anthony", "low", {"fs:read"})
    with pytest.raises(DelegationDenied, match="escalation"):
        orch.delegate(ctx, "high", {"fs:read", "exec:shell"})


def test_low_cannot_launder_through_high_agent(orch):
    ctx = orch.begin_delegation("anthony", "low", {"fs:read", "net:fetch"})
    with pytest.raises(DelegationDenied):
        orch.delegate(ctx, "high", {"secrets:read"}, human_approval=True)


def test_effective_is_three_way_intersection(orch):
    ctx = orch.begin_delegation("anthony", "mid", {"fs:read", "fs:write", "net:fetch"}, human_approval=True)
    child = orch.delegate(ctx, "low", {"fs:read", "fs:write", "net:fetch"}, human_approval=True)
    assert child.effective_scopes == frozenset({"fs:read", "net:fetch"})  # low lacks fs:write


def test_effective_scope_monotonically_shrinks(orch):
    orch.roster.register(card("wide", ["fs:read", "net:fetch"]))
    ctx = orch.begin_delegation("anthony", "mid", {"fs:read", "net:fetch"})
    c2 = orch.delegate(ctx, "low", {"fs:read"})
    with pytest.raises(DelegationDenied, match="escalation"):
        orch.delegate(c2, "wide", {"net:fetch"})  # regained scope not in parent's effective set


def test_loop_a_b_a_denied(orch):
    ctx = orch.begin_delegation("anthony", "mid", {"fs:read"})
    c2 = orch.delegate(ctx, "low", {"fs:read"})
    with pytest.raises(DelegationDenied, match="loop"):
        orch.delegate(c2, "mid", {"fs:read"})


def test_self_delegation_denied(orch):
    ctx = orch.begin_delegation("anthony", "mid", {"fs:read"})
    with pytest.raises(DelegationDenied, match="loop"):
        orch.delegate(ctx, "MID", {"fs:read"})


def test_loop_check_is_case_insensitive_via_ids(orch):
    ctx = orch.begin_delegation("anthony", "Mid", {"fs:read"})
    assert ctx.chain == ("mid",)


def test_default_depth_is_five():
    assert DEFAULT_MAX_DELEGATION_DEPTH == 5


def test_depth_exceeded_denied(orch):
    ctx = orch.begin_delegation("anthony", "n0", {"fs:read"})
    for i in range(1, 5):
        ctx = orch.delegate(ctx, f"n{i}", {"fs:read"})
    assert len(ctx.chain) == 5
    with pytest.raises(DelegationDenied, match="depth"):
        orch.delegate(ctx, "n5", {"fs:read"})


def test_custom_max_depth(orch):
    ctx = orch.begin_delegation("anthony", "n0", {"fs:read"}, max_depth=2)
    ctx = orch.delegate(ctx, "n1", {"fs:read"})
    with pytest.raises(DelegationDenied, match="depth"):
        orch.delegate(ctx, "n2", {"fs:read"})


@pytest.mark.parametrize("bad", [0, -1, None])
def test_invalid_max_depth_denied(orch, bad):
    with pytest.raises(DelegationDenied):
        orch.begin_delegation("anthony", "mid", {"fs:read"}, max_depth=bad)


def test_chain_records_originator(orch):
    ctx = orch.begin_delegation("anthony", "mid", {"fs:read"})
    ctx = orch.delegate(ctx, "low", {"fs:read"})
    assert ctx.originator == "anthony"
    assert ctx.chain == ("mid", "low")
    audit = ctx.to_audit()
    assert audit["originating_principal"] == "anthony"
    assert audit["delegation_chain"] == ["mid", "low"]


def test_chain_is_append_only_immutable(orch):
    ctx = orch.begin_delegation("anthony", "mid", {"fs:read"})
    child = orch.delegate(ctx, "low", {"fs:read"})
    assert ctx.chain == ("mid",)  # parent untouched
    assert child.chain[:1] == ctx.chain
    with pytest.raises(Exception):
        ctx.chain = ("evil",)  # frozen dataclass
    with pytest.raises(Exception):
        child.originator = "mallory"


def test_originator_required(orch):
    with pytest.raises(DelegationDenied):
        orch.begin_delegation("  ", "mid", {"fs:read"})


@pytest.mark.parametrize("scope", sorted(HIGH_IMPACT_SCOPES))
def test_high_impact_without_approval_denied(orch, scope):
    with pytest.raises(DelegationDenied, match="human approval"):
        orch.begin_delegation("anthony", "high", {scope})


@pytest.mark.parametrize("scope", sorted(HIGH_IMPACT_SCOPES))
def test_high_impact_with_approval_allowed(orch, scope):
    ctx = orch.begin_delegation("anthony", "high", {scope}, human_approval="TICKET-42")
    assert scope in ctx.effective_scopes


@pytest.mark.parametrize("bad", [None, False, "", "   ", 1, 0])
def test_non_token_approvals_rejected(orch, bad):
    with pytest.raises(DelegationDenied, match="human approval"):
        orch.begin_delegation("anthony", "high", {"fs:write"}, human_approval=bad)


def test_high_impact_deputy_hop_needs_approval_when_new(orch):
    ctx = orch.begin_delegation("anthony", "mid", {"fs:read"})
    # cannot request fs:write at deputy hop: not in parent's effective scope
    with pytest.raises(DelegationDenied):
        orch.delegate(ctx, "high", {"fs:write"}, human_approval=True)


def test_approved_high_impact_narrowing_inherits_approval(orch):
    ctx = orch.begin_delegation("anthony", "high", {"fs:write", "fs:read"}, human_approval="T1")
    child = orch.delegate(ctx, "mid", {"fs:write"})  # already approved at root
    assert child.effective_scopes == frozenset({"fs:write"})


def test_callee_with_none_of_requested_denied(orch):
    ctx = orch.begin_delegation("anthony", "mid", {"net:fetch"})
    with pytest.raises(DelegationDenied, match="none of"):
        orch.delegate(ctx, "n0", {"net:fetch"})


def test_legacy_card_defaults_unchanged():
    c = card("x")
    assert c.scopes is None
    assert c.authority == "CONSTITUTIONAL_GOVERNED"
    assert AgentCard.from_json({"agent_id": "X"}).scopes is None


def test_legacy_card_fail_closed_in_delegation(orch):
    with pytest.raises(DelegationDenied):
        orch.begin_delegation("anthony", "legacy", {"fs:read"})
    ctx = orch.begin_delegation("anthony", "legacy")  # scope-less delegation OK
    assert ctx.effective_scopes == frozenset()


def test_unknown_agent_holds_no_scopes(orch):
    with pytest.raises(DelegationDenied):
        orch.begin_delegation("anthony", "ghost", {"fs:read"})


def test_scopes_normalized_and_from_json():
    c = AgentCard.from_json({"agent_id": "A", "scopes": ["fs:read", " fs:read ", "net:fetch"]})
    assert c.scopes == frozenset({"fs:read", "net:fetch"})
    assert isinstance(c.scopes, frozenset)


def test_scopes_reject_bare_string_and_blank():
    with pytest.raises(TypeError):
        card("x", "fs:write")
    with pytest.raises(ValueError):
        card("x", ["  "])


def test_legacy_governed_task_unchanged_without_delegation(orch):
    res = orch.execute_governed_task("legacy", "vance", "t", SAFE)
    assert res["success"] is True
    assert "delegation_chain" not in res and "originating_principal" not in res


def test_receipt_shows_original_principal_not_last_deputy(orch):
    ctx = orch.begin_delegation("anthony", "mid", {"fs:read", "net:fetch"})
    ctx = orch.delegate(ctx, "low", {"fs:read"})
    res = orch.execute_governed_task("low", "vance", "t", SAFE, delegation=ctx)
    assert res["success"] is True
    assert res["originating_principal"] == "anthony"
    assert res["delegation_chain"] == ["mid", "low"]
    assert any(
        s.payload.get("originating_principal") == "anthony" and s.payload.get("delegation_chain") == ["mid", "low"]
        for s in orch.history
    )


def test_governed_task_denied_when_worker_not_current_deputy(orch):
    ctx = orch.begin_delegation("anthony", "low", {"fs:read"})
    res = orch.execute_governed_task("high", "vance", "t", SAFE, delegation=ctx)
    assert res["success"] is False
    assert res["stage"] == "DELEGATION_DENIED"
    assert res["originating_principal"] == "anthony"


def test_governed_task_write_denied_without_fs_write_scope(orch, tmp_path):
    ctx = orch.begin_delegation("anthony", "low", {"fs:read"})
    res = orch.execute_governed_task("low", "vance", "t", SAFE, target_path=str(tmp_path / "o.py"), delegation=ctx)
    assert res["success"] is False and res["stage"] == "DELEGATION_DENIED"
    assert not (tmp_path / "o.py").exists()
