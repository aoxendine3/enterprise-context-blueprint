"""
XORAS Systems LLC — Agent Identity & Council Roster Engine
Ingests, verifies, and executes canonical sovereign agent cards.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, FrozenSet, Iterable, List, Optional


def _normalize_scopes(scopes: Iterable[str]) -> FrozenSet[str]:
    if isinstance(scopes, (str, bytes)):
        raise TypeError("scopes must be an iterable of strings, not a single string")
    out = set()
    for sc in scopes:
        if not isinstance(sc, str) or not sc.strip():
            raise ValueError(f"invalid scope: {sc!r}")
        out.add(sc.strip())
    return frozenset(out)


@dataclass
class AgentCard:
    agent_id: str
    name: str
    role: str
    seat: int
    status: str
    purpose: str
    voice: Optional[str] = None
    kokoro_voice_id: Optional[str] = None
    isolation_level: str = "ZERO_BLEED_CAPSULE_ISOLATED"
    authority: str = "CONSTITUTIONAL_GOVERNED"
    tools: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Delegation scopes (e.g. "fs:write"). None == LEGACY card with no declared
    # scopes: legacy execution paths are unchanged, but in the delegation API a
    # legacy card is treated as holding the EMPTY scope set (fail-closed), so it
    # can neither delegate nor receive any non-empty scope. Wildcards unsupported.
    scopes: Optional[FrozenSet[str]] = None

    def __post_init__(self) -> None:
        if self.scopes is not None:
            self.scopes = _normalize_scopes(self.scopes)

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> AgentCard:
        return cls(
            agent_id=data.get("agent_id", "unknown").lower(),
            name=data.get("name", "Unknown Agent"),
            role=data.get("role", "General Specialist"),
            seat=int(data.get("seat", 0)),
            status=data.get("status", "ACTIVE"),
            purpose=data.get("purpose", ""),
            voice=data.get("voice"),
            kokoro_voice_id=data.get("kokoro_voice_id"),
            isolation_level=data.get("isolation_level", "ZERO_BLEED_CAPSULE_ISOLATED"),
            authority=data.get("authority", "CONSTITUTIONAL_GOVERNED"),
            tools=data.get("tools", []),
            metadata=data.get("metadata", {}),
            scopes=data.get("scopes"),
        )

    @classmethod
    def from_file(cls, path: str | Path) -> AgentCard:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_json(data)


class AgentRoster:
    """Manages verified sovereign agent registries."""

    def __init__(self) -> None:
        self.cards: Dict[str, AgentCard] = {}

    def register(self, card: AgentCard) -> None:
        self.cards[card.agent_id.lower()] = card

    def get(self, agent_id: str) -> Optional[AgentCard]:
        return self.cards.get(agent_id.lower())

    def list_agents(self) -> List[AgentCard]:
        return sorted(self.cards.values(), key=lambda c: c.seat)

    def load_from_directory(self, dir_path: str | Path) -> int:
        p = Path(dir_path)
        if not p.exists() or not p.is_dir():
            return 0

        loaded = 0
        for card_file in p.glob("*.json"):
            try:
                card = AgentCard.from_file(card_file)
                self.register(card)
                loaded += 1
            except Exception:
                continue
        return loaded
