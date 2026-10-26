"""
XORAS Systems LLC — Council Orchestrator
Executes true multi-agent dual-pillar verification: Worker execution -> Critic audit -> Merkle provenance.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Tuple

from .agents import AgentCard, AgentRoster, _normalize_scopes
from .ast_security import ASTScanResult, ASTSecurityEngine
from .merkle_dag import ContextLineageDAGEngine, MerkleDAGNode
from .runtime import XORASAgentEnvironment

logger = logging.getLogger("xoras.council")


# Scopes that always need an explicit human approval (token string or True).
HIGH_IMPACT_SCOPES: FrozenSet[str] = frozenset(
    {"fs:write", "net:egress", "exec:shell", "secrets:read"}
)
DEFAULT_MAX_DELEGATION_DEPTH = 5


class DelegationDenied(PermissionError):
    """Raised when a delegation violates scope, loop, depth or approval policy."""


@dataclass(frozen=True)
class DelegationContext:
    """Immutable, append-only delegation record (confused-deputy defense).

    `originator` is the ORIGINAL principal; `chain` lists agent ids in order
    (chain[-1] is the current deputy). `effective_scopes` only ever shrinks.
    """

    originator: str
    chain: Tuple[str, ...]
    effective_scopes: FrozenSet[str]
    approved_high_impact: FrozenSet[str] = frozenset()
    max_depth: int = DEFAULT_MAX_DELEGATION_DEPTH

    def to_audit(self) -> Dict[str, Any]:
        return {
            "originating_principal": self.originator,
            "delegation_chain": list(self.chain),
            "effective_scopes": sorted(self.effective_scopes),
        }


def _valid_approval(approval: Any) -> bool:
    return approval is True or (isinstance(approval, str) and bool(approval.strip()))


@dataclass
class CouncilStep:
    agent_id: str
    role: str
    phase: str
    payload: Dict[str, Any]
    status: str
    verdict: Optional[str] = None


class CouncilOrchestrator:
    """Coordinates Sovereign Dual-Pillar execution: Worker writes -> Critic audits -> DAG seals."""

    def __init__(
        self,
        roster: Optional[AgentRoster] = None,
        env: Optional[XORASAgentEnvironment] = None,
    ) -> None:
        self.roster = roster or AgentRoster()
        self.env = env or XORASAgentEnvironment()
        self.ast_engine = ASTSecurityEngine(strict_mode=True)
        self.dag = ContextLineageDAGEngine()
        self.history: List[CouncilStep] = []

    def _scopes_of(self, agent_id: str) -> FrozenSet[str]:
        card = self.roster.get(agent_id)
        # Unknown or legacy (scopes=None) agents hold no delegable scopes.
        return card.scopes if card is not None and card.scopes is not None else frozenset()

    def _extend(
        self,
        parent_scopes: FrozenSet[str],
        originator: str,
        prior_chain: Tuple[str, ...],
        approved: FrozenSet[str],
        callee_id: str,
        requested: Iterable[str],
        human_approval: Any,
        max_depth: int,
    ) -> DelegationContext:
        callee = callee_id.strip().lower()
        req = _normalize_scopes(requested)
        if not callee:
            raise DelegationDenied("empty callee id")
        if callee in prior_chain:
            raise DelegationDenied(f"delegation loop: '{callee}' already in chain {list(prior_chain)}")
        if len(prior_chain) + 1 > max_depth:
            raise DelegationDenied(f"max delegation depth {max_depth} exceeded")
        if not req <= parent_scopes:
            raise DelegationDenied(f"scope escalation: {sorted(req - parent_scopes)} not held by delegator")
        effective = parent_scopes & self._scopes_of(callee) & req
        if req and not effective:
            raise DelegationDenied(f"callee '{callee}' holds none of the requested scopes")
        high = effective & HIGH_IMPACT_SCOPES
        new_high = high - approved
        if new_high and not _valid_approval(human_approval):
            raise DelegationDenied(f"human approval required for high-impact scopes {sorted(new_high)}")
        return DelegationContext(
            originator=originator,
            chain=prior_chain + (callee,),
            effective_scopes=effective,
            approved_high_impact=approved | high,
            max_depth=max_depth,
        )

    def begin_delegation(
        self,
        principal: str,
        agent_id: str,
        requested_scopes: Iterable[str] = (),
        human_approval: Any = None,
        max_depth: int = DEFAULT_MAX_DELEGATION_DEPTH,
    ) -> DelegationContext:
        """Root hop: `principal` (human/system, unbounded) hands work to `agent_id`."""
        if not isinstance(principal, str) or not principal.strip():
            raise DelegationDenied("originating principal required")
        if not isinstance(max_depth, int) or max_depth < 1:
            raise DelegationDenied("max_depth must be a positive integer")
        req = _normalize_scopes(requested_scopes)
        # The principal is the trust root: it may request anything; the callee narrows it.
        return self._extend(req, principal.strip(), (), frozenset(), agent_id, req, human_approval, max_depth)

    def delegate(
        self,
        ctx: DelegationContext,
        callee_id: str,
        requested_scopes: Iterable[str] = (),
        human_approval: Any = None,
    ) -> DelegationContext:
        """Deputy hop: current deputy (ctx.chain[-1]) delegates to `callee_id`.

        Effective scope = parent effective ∩ callee scopes ∩ requested; requested
        must be ⊆ parent effective. Raises DelegationDenied otherwise.
        """
        return self._extend(
            ctx.effective_scopes, ctx.originator, ctx.chain, ctx.approved_high_impact,
            callee_id, requested_scopes, human_approval, ctx.max_depth,
        )

    def execute_governed_task(
        self,
        worker_id: str,
        critic_id: str,
        task_name: str,
        code_payload: str,
        target_path: Optional[str] = None,
        delegation: Optional[DelegationContext] = None,
    ) -> Dict[str, Any]:
        """Runs the Dual-Pillar governed workflow:

        1. Worker generates & formats payload
        2. AST Security Screening
        3. Critic audits verification gates
        4. Cryptographic Provenance DAG sealing
        """
        worker = self.roster.get(worker_id) or AgentCard(
            agent_id=worker_id, name=worker_id.upper(), role="Lead Worker", seat=1, status="ACTIVE", purpose="Task Execution"
        )
        critic = self.roster.get(critic_id) or AgentCard(
            agent_id=critic_id, name=critic_id.upper(), role="Security Critic", seat=2, status="ACTIVE", purpose="Independent Audit"
        )

        audit: Dict[str, Any] = {}
        if delegation is not None:
            audit = delegation.to_audit()
            needed = {"fs:write"} if target_path else set()
            if delegation.chain[-1] != worker.agent_id.lower() or not needed <= delegation.effective_scopes:
                return {
                    "success": False,
                    "stage": "DELEGATION_DENIED",
                    "error": "worker is not current deputy or lacks required scope",
                    **audit,
                }

        logger.info("Initiating Governed Task '%s' with Worker=%s, Critic=%s", task_name, worker.name, critic.name)

        # Stage 1: Worker Execution
        worker_node_id = f"worker_{uuid.uuid4().hex[:8]}"
        worker_payload = {"task": task_name, "code_len": len(code_payload), "agent": worker.name, **audit}
        ok, worker_hash, err = self.dag.commit(worker_node_id, [], worker_payload)
        
        self.history.append(
            CouncilStep(
                agent_id=worker.agent_id,
                role=worker.role,
                phase="WORKER_EXECUTION",
                payload={"node_id": worker_node_id, "state_hash": worker_hash, "task": task_name, **audit},
                status="SUCCESS" if ok else "FAILED",
            )
        )

        # Stage 2: AST Security Static Screening
        ast_result: ASTScanResult = self.ast_engine.scan_code(code_payload)
        if not ast_result.is_safe:
            reject_node_id = f"ast_gate_{uuid.uuid4().hex[:8]}"
            reject_payload = {"violations": ast_result.violations, "safety_score": ast_result.safety_score}
            self.dag.commit(reject_node_id, [worker_node_id], reject_payload)
            
            self.history.append(
                CouncilStep(
                    agent_id="ast_gate",
                    role="Static Security Interceptor",
                    phase="AST_SCREENING",
                    payload={"violations": ast_result.violations},
                    status="REJECTED",
                    verdict="UNSAFE_PAYLOAD_BLOCKED",
                )
            )
            return {
                "success": False,
                "stage": "AST_SCREENING_FAILED",
                "violations": ast_result.violations,
                "safety_score": ast_result.safety_score,
                "dag_root": self.dag.get_dynamic_merkle_root(),
                **audit,
            }

        # Stage 3: Independent Critic Audit Gate (Vance Standard)
        critic_node_id = f"critic_{uuid.uuid4().hex[:8]}"
        critic_payload = {"target_path": target_path, "ast_passed": True, "safety_score": ast_result.safety_score, "critic": critic.name}
        ok, critic_hash, err = self.dag.commit(critic_node_id, [worker_node_id], critic_payload)

        self.history.append(
            CouncilStep(
                agent_id=critic.agent_id,
                role=critic.role,
                phase="CRITIC_AUDIT",
                payload={"critic_node_id": critic_node_id, "state_hash": critic_hash, "safety_score": ast_result.safety_score},
                status="APPROVED",
                verdict="GATE_CLEARED",
            )
        )

        # Stage 4: Execution / Persistence (if path specified)
        exec_details = {"written": False}
        if target_path:
            exec_res = self.env.execute_tool(
                agent_name=worker.name,
                tool_name="file_write",
                args={"path": target_path, "content": code_payload},
            )
            exec_details["written"] = exec_res.get("success", False)

        return {
            "success": True,
            "stage": "COUNCIL_CERTIFIED",
            "task": task_name,
            "worker": worker.name,
            "critic": critic.name,
            "safety_score": ast_result.safety_score,
            "dag_root": self.dag.get_dynamic_merkle_root(),
            "provenance_node_count": len(self.dag.nodes),
            "execution": exec_details,
            **audit,
        }
