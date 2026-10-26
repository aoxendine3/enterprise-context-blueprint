"""
Unit tests for XORAS Agent Cards, Roster Loader, and Council Orchestrator.
"""

import os
import pytest
from xoras.agents import AgentCard, AgentRoster
from xoras.council import CouncilOrchestrator
from xoras.runtime import XORASAgentEnvironment


def test_agent_card_instantiation():
    card = AgentCard(
        agent_id="daxx",
        name="DAXX.AI",
        role="Master Mechanic Specialist & Coding Specialist",
        seat=3,
        status="SOVEREIGN_CITIZEN_ACTIVE",
        purpose="Comprehensive mechanical & software mastery",
        voice="Lee (Premium)",
    )
    assert card.agent_id == "daxx"
    assert card.seat == 3
    assert card.isolation_level == "ZERO_BLEED_CAPSULE_ISOLATED"


def test_agent_roster_registration():
    roster = AgentRoster()
    c1 = AgentCard(agent_id="maxx", name="Maxx", role="Operations", seat=1, status="ACTIVE", purpose="Ops")
    c2 = AgentCard(agent_id="vance", name="Vance", role="Auditor", seat=2, status="ACTIVE", purpose="Audit")
    roster.register(c1)
    roster.register(c2)

    assert roster.get("MAXX") is not None
    assert roster.get("vance").name == "Vance"
    assert len(roster.list_agents()) == 2
    assert roster.list_agents()[0].agent_id == "maxx"


def test_council_governed_task_pass():
    roster = AgentRoster()
    daxx = AgentCard(agent_id="daxx", name="DAXX.AI", role="Mechanic", seat=3, status="ACTIVE", purpose="Coding")
    vance = AgentCard(agent_id="vance", name="William Vance", role="Critic", seat=2, status="ACTIVE", purpose="Audit")
    roster.register(daxx)
    roster.register(vance)

    orchestrator = CouncilOrchestrator(roster=roster)
    safe_code = """
def clean_add(a: int, b: int) -> int:
    return a + b
"""
    result = orchestrator.execute_governed_task(
        worker_id="daxx",
        critic_id="vance",
        task_name="implement_addition",
        code_payload=safe_code,
    )

    assert result["success"] is True
    assert result["stage"] == "COUNCIL_CERTIFIED"
    assert result["worker"] == "DAXX.AI"
    assert result["critic"] == "William Vance"
    assert result["safety_score"] == 1.0
    assert result["dag_root"] is not None
    assert result["provenance_node_count"] >= 2


def test_council_governed_task_ast_rejection():
    roster = AgentRoster()
    orchestrator = CouncilOrchestrator(roster=roster)
    malicious_code = """
import os
eval("__import__('os').system('rm -rf /')")
"""
    result = orchestrator.execute_governed_task(
        worker_id="daxx",
        critic_id="vance",
        task_name="unsafe_eval_injection",
        code_payload=malicious_code,
    )

    assert result["success"] is False
    assert result["stage"] == "AST_SCREENING_FAILED"
    assert len(result["violations"]) > 0
    assert any("eval()" in v for v in result["violations"])
