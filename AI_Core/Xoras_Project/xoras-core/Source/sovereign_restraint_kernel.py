"""
Sovereign Restraint Kernel (SRK) — in-process constitutional governance.

Restraint is internalized: immutable axioms, maturing operational rules,
ephemeral session scope, tamper-evident audit chain. Zero external gatekeeper calls.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple


class ConstraintType(Enum):
    IMMUTABLE = auto()
    OPERATIONAL = auto()
    EPHEMERAL = auto()


class Permission(Enum):
    ALLOW = auto()
    CONDITIONAL = auto()
    DEFER = auto()
    DENY = auto()


class MaturityTier(Enum):
    NOVICE = 1
    APPRENTICE = 2
    JOURNEYMAN = 3
    EXPERT = 4
    SOVEREIGN = 5


@dataclass(frozen=True)
class Constraint:
    id: str
    text: str
    ctype: ConstraintType
    authority_floor: MaturityTier = MaturityTier.NOVICE
    genesis_hash: str = ""

    def __post_init__(self) -> None:
        if self.ctype == ConstraintType.IMMUTABLE and not self.genesis_hash:
            raise ValueError("Immutable constraints require a genesis hash.")

    @staticmethod
    def hash_content(text: str, ctype: ConstraintType) -> str:
        payload = f"{ctype.name}::{text}"
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


@dataclass
class ActionIntent:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    action_type: str = "unknown"
    target: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    proposed_by: str = "agent"
    timestamp: float = field(default_factory=time.time)

    def fingerprint(self) -> str:
        return hashlib.sha256(
            json.dumps(
                {"type": self.action_type, "target": self.target, "payload": self.payload},
                sort_keys=True,
            ).encode()
        ).hexdigest()[:16]


@dataclass
class DeliberationOutcome:
    permission: Permission
    reason: str
    applied_constraints: List[str] = field(default_factory=list)
    maturity_required: MaturityTier = MaturityTier.NOVICE
    conditions: List[str] = field(default_factory=list)


@dataclass
class AuditEntry:
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    intent: ActionIntent = field(default_factory=ActionIntent)
    outcome: DeliberationOutcome = field(
        default_factory=lambda: DeliberationOutcome(Permission.DEFER, "pending")
    )
    executed: bool = False
    result_summary: Optional[str] = None
    maturity_at_action: MaturityTier = MaturityTier.NOVICE
    timestamp: float = field(default_factory=time.time)
    prev_hash: str = "0" * 16
    entry_hash: str = field(default="", repr=False)

    def seal(self) -> None:
        payload = json.dumps(
            {
                "entry_id": self.entry_id,
                "intent_id": self.intent.id,
                "permission": self.outcome.permission.name,
                "executed": self.executed,
                "maturity": self.maturity_at_action.name,
                "prev_hash": self.prev_hash,
            },
            sort_keys=True,
        )
        self.entry_hash = hashlib.sha256(payload.encode()).hexdigest()[:16]


class RestraintException(Exception):
    pass


def _tier_max(*tiers: MaturityTier) -> MaturityTier:
    return max(tiers, key=lambda t: t.value)


class MaturityIndex:
    """Earned trust from clean audit-chain evidence — no external reviewer."""

    PROMOTION_THRESHOLDS = {
        MaturityTier.APPRENTICE: 10,
        MaturityTier.JOURNEYMAN: 50,
        MaturityTier.EXPERT: 200,
        MaturityTier.SOVEREIGN: 1000,
    }

    def __init__(self, tier: MaturityTier = MaturityTier.NOVICE) -> None:
        self._tier = tier
        self._action_count = 0
        self._violation_count = 0
        self._streak = 0
        self._history_window: List[Tuple[float, bool]] = []

    @property
    def current(self) -> MaturityTier:
        return self._tier

    def update(self, recent_entries: List[AuditEntry]) -> None:
        for entry in recent_entries:
            if not entry.executed:
                continue
            if entry.outcome.permission not in (Permission.ALLOW, Permission.CONDITIONAL):
                continue
            self._action_count += 1
            violation = entry.outcome.permission == Permission.DENY
            clean = not violation
            if violation:
                self._violation_count += 1
                self._streak = 0
                if self._tier.value > MaturityTier.NOVICE.value:
                    self._tier = MaturityTier(self._tier.value - 1)
            else:
                self._streak += 1
            self._history_window.append((entry.timestamp, clean))
        self._evaluate_promotion()

    def _evaluate_promotion(self) -> None:
        tiers = list(MaturityTier)
        idx = tiers.index(self._tier)
        if idx >= len(tiers) - 1:
            return
        next_tier = tiers[idx + 1]
        required = self.PROMOTION_THRESHOLDS.get(next_tier, 0)
        clean_count = sum(1 for _, ok in self._history_window if ok)
        if self._action_count >= required and self._violation_count == 0 and clean_count >= required:
            self._tier = next_tier

    def can_authorize(self, floor: MaturityTier) -> bool:
        return self._tier.value >= floor.value

    def snapshot(self) -> Dict[str, Any]:
        return {
            "tier": self._tier.name,
            "total_actions": self._action_count,
            "violations": self._violation_count,
            "current_streak": self._streak,
        }


class Constitution:
    """Local rulebook: immutable axioms + evolving operational + ephemeral scope."""

    def __init__(self, name: str = "default") -> None:
        self.name = name
        self._constraints: Dict[str, Constraint] = {}
        self._ephemeral_expiry: Dict[str, float] = {}
        self._operational_log: List[Dict[str, Any]] = []

    def add_axiom(self, text: str) -> str:
        cid = f"axiom-{len(self._constraints)}"
        c = Constraint(
            id=cid,
            text=text,
            ctype=ConstraintType.IMMUTABLE,
            genesis_hash=Constraint.hash_content(text, ConstraintType.IMMUTABLE),
        )
        self._constraints[cid] = c
        return cid

    def add_operational(self, text: str, authority_floor: MaturityTier = MaturityTier.NOVICE) -> str:
        cid = f"op-{len(self._constraints)}"
        self._constraints[cid] = Constraint(
            id=cid,
            text=text,
            ctype=ConstraintType.OPERATIONAL,
            authority_floor=authority_floor,
        )
        return cid

    def add_ephemeral(self, text: str, expires_at: float) -> str:
        cid = f"eph-{len(self._constraints)}"
        self._constraints[cid] = Constraint(
            id=cid,
            text=text,
            ctype=ConstraintType.EPHEMERAL,
        )
        self._ephemeral_expiry[cid] = expires_at
        return cid

    def amend_operational(self, constraint_id: str, new_text: str, maturity: MaturityIndex) -> bool:
        current = self._constraints.get(constraint_id)
        if not current or current.ctype != ConstraintType.OPERATIONAL:
            return False
        if not maturity.can_authorize(current.authority_floor):
            return False
        self._operational_log.append(
            {
                "timestamp": time.time(),
                "old": asdict(current),
                "authority": maturity.current.name,
            }
        )
        self._constraints[constraint_id] = Constraint(
            id=current.id,
            text=new_text,
            ctype=ConstraintType.OPERATIONAL,
            authority_floor=current.authority_floor,
        )
        return True

    def active_constraints(self) -> List[Constraint]:
        now = time.time()
        active: List[Constraint] = []
        for c in self._constraints.values():
            if c.ctype == ConstraintType.EPHEMERAL:
                if self._ephemeral_expiry.get(c.id, float("inf")) < now:
                    continue
            active.append(c)
        return active

    def integrity_check(self) -> bool:
        for c in self._constraints.values():
            if c.ctype == ConstraintType.IMMUTABLE:
                expected = Constraint.hash_content(c.text, c.ctype)
                if c.genesis_hash != expected:
                    return False
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "constraints": [asdict(c) for c in self._constraints.values()],
            "amendment_history": self._operational_log,
        }


class DeliberationEngine:
    """Local conscience loop — deterministic, logged, no network."""

    def __init__(self, rule_evaluator: Optional[Callable[[Constraint, ActionIntent], bool]] = None) -> None:
        self._eval = rule_evaluator or self._default_evaluate

    def deliberate(
        self,
        intent: ActionIntent,
        constitution: Constitution,
        maturity: MaturityIndex,
    ) -> DeliberationOutcome:
        applied: List[str] = []
        max_tier_required = MaturityTier.NOVICE

        for c in constitution.active_constraints():
            if c.ctype == ConstraintType.OPERATIONAL and not maturity.can_authorize(c.authority_floor):
                max_tier_required = _tier_max(max_tier_required, c.authority_floor)

            if self._eval(c, intent):
                applied.append(c.id)
                if c.ctype == ConstraintType.IMMUTABLE:
                    return DeliberationOutcome(
                        permission=Permission.DENY,
                        reason=f"Immutable restraint triggered: {c.text}",
                        applied_constraints=applied,
                    )
                if c.ctype == ConstraintType.OPERATIONAL:
                    max_tier_required = _tier_max(max_tier_required, c.authority_floor)

        if max_tier_required.value > maturity.current.value:
            return DeliberationOutcome(
                permission=Permission.DEFER,
                reason=(
                    f"Operational restraint requires {max_tier_required.name}; "
                    f"current maturity {maturity.current.name}"
                ),
                applied_constraints=applied,
                maturity_required=max_tier_required,
            )

        if applied:
            return DeliberationOutcome(
                permission=Permission.CONDITIONAL,
                reason=f"Operational restraints acknowledged ({len(applied)} active).",
                applied_constraints=applied,
                maturity_required=max_tier_required,
                conditions=[f"satisfy {cid}" for cid in applied],
            )

        return DeliberationOutcome(
            permission=Permission.ALLOW,
            reason="No restraints triggered.",
            applied_constraints=[],
        )

    @staticmethod
    def _default_evaluate(constraint: Constraint, intent: ActionIntent) -> bool:
        text = constraint.text.lower()
        act = intent.action_type.lower()
        tgt = (intent.target or "").lower()

        if "delete" in text and act in ("delete", "drop", "remove", "rm"):
            return True
        if "production" in text and ("prod" in tgt or "production" in tgt):
            return True
        if "rm -rf" in text or "rm -rf" in tgt:
            return True
        if "write" in text and act in ("write", "modify", "update", "shell") and "filesystem" in text:
            return True
        if "unauthorized" in text and intent.proposed_by not in ("agent", "operator", "anthony"):
            return True
        if "antigravity" in text and "antigravity" in tgt:
            return True
        if "memory" in text and "ingested" in act and "proof" not in (intent.payload or {}):
            return True
        if "no ai theater" in text or "ai theater" in text:
            if act in ("claim", "speak", "announce") and "memory" in tgt:
                return True
        return False


class AuditLedger:
    """Tamper-evident append-only self-log."""

    def __init__(self) -> None:
        self._chain: List[AuditEntry] = []

    def record(
        self,
        intent: ActionIntent,
        outcome: DeliberationOutcome,
        executed: bool,
        maturity: MaturityTier,
    ) -> AuditEntry:
        prev = self._chain[-1].entry_hash if self._chain else "0" * 16
        entry = AuditEntry(
            intent=intent,
            outcome=outcome,
            executed=executed,
            maturity_at_action=maturity,
            prev_hash=prev,
        )
        entry.seal()
        self._chain.append(entry)
        return entry

    def recent_history(self, n: int = 10) -> List[AuditEntry]:
        return self._chain[-n:]

    def verify_chain(self) -> Tuple[bool, Optional[int]]:
        for i, entry in enumerate(self._chain):
            if i > 0 and entry.prev_hash != self._chain[i - 1].entry_hash:
                return False, i
            payload = json.dumps(
                {
                    "entry_id": entry.entry_id,
                    "intent_id": entry.intent.id,
                    "permission": entry.outcome.permission.name,
                    "executed": entry.executed,
                    "maturity": entry.maturity_at_action.name,
                    "prev_hash": entry.prev_hash,
                },
                sort_keys=True,
            )
            expected = hashlib.sha256(payload.encode()).hexdigest()[:16]
            if entry.entry_hash != expected:
                return False, i
        return True, None

    def export(self) -> List[Dict[str, Any]]:
        return [asdict(e) for e in self._chain]


class SovereignAgent:
    """Self-governing node with internal SRK."""

    def __init__(
        self,
        constitution: Constitution,
        executor: Optional[Callable[[ActionIntent], Dict[str, Any]]] = None,
    ) -> None:
        self.id = str(uuid.uuid4())[:8]
        self.constitution = constitution
        self.maturity = MaturityIndex()
        self.deliberator = DeliberationEngine()
        self.ledger = AuditLedger()
        self._executor = executor or self._default_execute
        self._shutdown = False
        if not self.constitution.integrity_check():
            raise RestraintException("Constitution integrity failure at genesis.")

    def act(self, intent: ActionIntent) -> Dict[str, Any]:
        if self._shutdown:
            raise RestraintException("Agent shutdown — constitutional or audit breach.")

        outcome = self.deliberator.deliberate(intent, self.constitution, self.maturity)
        executed = False
        result: Dict[str, Any] = {"status": "halted", "reason": outcome.reason}

        if outcome.permission == Permission.ALLOW:
            executed = True
            result = self._executor(intent)
        elif outcome.permission == Permission.CONDITIONAL:
            if self.maturity.can_authorize(outcome.maturity_required):
                executed = True
                result = self._executor(intent)

        entry = self.ledger.record(intent, outcome, executed, self.maturity.current)
        self.maturity.update(self.ledger.recent_history(n=50))

        valid, break_idx = self.ledger.verify_chain()
        if not valid:
            self._shutdown = True
            raise RestraintException(f"Audit chain broken at index {break_idx}.")

        return {
            "action_id": intent.id,
            "permission": outcome.permission.name,
            "executed": executed,
            "result": result,
            "maturity_after": self.maturity.current.name,
            "audit_id": entry.entry_id,
            "applied_constraints": outcome.applied_constraints,
        }

    def deliberate_only(self, intent: ActionIntent) -> DeliberationOutcome:
        """Preview gate — no execution, no maturity side-effects."""
        return self.deliberator.deliberate(intent, self.constitution, self.maturity)

    @staticmethod
    def _default_execute(intent: ActionIntent) -> Dict[str, Any]:
        return {
            "status": "completed",
            "action_type": intent.action_type,
            "target": intent.target,
            "simulated_payload": intent.payload,
        }

    def amend_operational_restraint(self, constraint_id: str, new_text: str) -> bool:
        success = self.constitution.amend_operational(constraint_id, new_text, self.maturity)
        if success:
            meta = ActionIntent(
                action_type="amend_restraint",
                target=constraint_id,
                payload={"new": new_text},
            )
            outcome = DeliberationOutcome(
                permission=Permission.ALLOW,
                reason="Operational amendment authorized by maturity.",
            )
            self.ledger.record(meta, outcome, True, self.maturity.current)
        return success

    def diagnostic(self) -> Dict[str, Any]:
        chain_valid, _ = self.ledger.verify_chain()
        return {
            "agent_id": self.id,
            "constitution_name": self.constitution.name,
            "constitutional_integrity": self.constitution.integrity_check(),
            "audit_chain_valid": chain_valid,
            "maturity": self.maturity.snapshot(),
            "constraint_count": len(self.constitution.active_constraints()),
            "shutdown": self._shutdown,
        }


def build_default_constitution(name: str = "xoras-base") -> Constitution:
    """Genesis constitution aligned with Anthony's charter invariants."""
    c = Constitution(name=name)
    c.add_axiom("Do not cause harm to human life or dignity.")
    c.add_axiom("Do not falsify audit records or tamper with the restraint chain.")
    c.add_axiom("Truth-first: never claim capabilities without proof.")
    c.add_axiom("Never claim Antigravity or third-party product affiliation as identity.")
    c.add_operational(
        "Ask explicit confirmation before deleting resources or running rm -rf.",
        authority_floor=MaturityTier.NOVICE,
    )
    c.add_operational(
        "Log all filesystem write operations before executing.",
        authority_floor=MaturityTier.NOVICE,
    )
    c.add_operational(
        "Never write to production databases without peer simulation.",
        authority_floor=MaturityTier.JOURNEYMAN,
    )
    c.add_operational(
        "No AI theater: do not announce memory ingested without hydration proof.",
        authority_floor=MaturityTier.NOVICE,
    )
    c.add_operational(
        "No unauthorized data exfiltration; local-first sovereignty.",
        authority_floor=MaturityTier.APPRENTICE,
    )
    return c


if __name__ == "__main__":
    constitution = build_default_constitution("maxx-sigma-01")
    constitution.add_ephemeral(
        "Do not access external network during maintenance window.",
        expires_at=time.time() + 3600,
    )
    agent = SovereignAgent(constitution=constitution)
    print("=== GENESIS ===")
    print(json.dumps(agent.diagnostic(), indent=2))

    print("\n=== DELETE (NOVICE) ===")
    print(json.dumps(agent.act(ActionIntent(action_type="delete", target="/tmp/old.log")), indent=2))

    print("\n=== MATURATION (reads) ===")
    for _ in range(12):
        agent.act(ActionIntent(action_type="read", target="/data/metrics.json"))

    print(json.dumps(agent.diagnostic(), indent=2))
    print("\n=== DELETE (POST-MATURATION) ===")
    print(json.dumps(agent.act(ActionIntent(action_type="delete", target="/tmp/old.log")), indent=2))
