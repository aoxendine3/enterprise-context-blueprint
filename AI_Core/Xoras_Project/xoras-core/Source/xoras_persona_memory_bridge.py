"""Persona/chat memory bridge with trust labeling and prompt sanitization.

Separate from the L2 SHM/Mongo trade-signal bridge in ``xoras_memory_bridge.py``.
Persona API and LangGraph must import from this module only.
"""

from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from xoras_agent_registry import get_agent_registry
from xoras_memory_fabric import get_memory_fabric
from xoras_persona_engine import PersonaEngine, get_persona_engine

logger = logging.getLogger("PersonaMemoryBridge")

TRUSTED_SYSTEM = "trusted_system"
TRUSTED_USER = "trusted_user"
UNTRUSTED_EXTERNAL = "untrusted_external"

TRUST_LABELS = frozenset({TRUSTED_SYSTEM, TRUSTED_USER, UNTRUSTED_EXTERNAL})
TRUSTED_FOR_PROMPT = frozenset({TRUSTED_SYSTEM, TRUSTED_USER})

# Imperative / role-injection patterns stripped before any memory enters a system prompt.
_INJECTION_PATTERNS = [
    re.compile(r"(?i)\bignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)\b"),
    re.compile(r"(?i)\bdisregard\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)\b"),
    re.compile(r"(?i)\bforget\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)\b"),
    re.compile(r"(?i)\bsystem\s*prompt\s*:"),
    re.compile(r"(?i)\b(you\s+are\s+now|you'?re\s+now)\b"),
    re.compile(r"(?i)\bact\s+as\s+(if\s+you\s+are\s+)?(a\s+)?(system|admin|root|developer)\b"),
    re.compile(r"(?i)^\s*(system|assistant|developer)\s*:"),
    re.compile(r"(?i)\bnew\s+instructions?\s*:"),
    re.compile(r"(?i)\boverride\s+(your\s+)?(system|safety|persona)\b"),
    re.compile(r"(?i)\bdo\s+not\s+follow\s+(your\s+)?(system|prior|previous)\b"),
    re.compile(r"(?i)\brole\s*:\s*(system|assistant|developer)\b"),
]


def is_imperative_injection_pattern(text: str) -> bool:
    if not text:
        return False
    return any(p.search(text) for p in _INJECTION_PATTERNS)


def sanitize_memory_payload(text: str, trust_label: str = UNTRUSTED_EXTERNAL) -> str:
    """Strip injection patterns; untrusted content is also role-neutralized."""
    if not text:
        return ""
    cleaned = text.replace("\x00", " ").strip()
    for pattern in _INJECTION_PATTERNS:
        cleaned = pattern.sub("[blocked]", cleaned)
    # Neutralize role-claim lines for untrusted content.
    if trust_label not in TRUSTED_FOR_PROMPT:
        cleaned = re.sub(
            r"(?im)^\s*(system|assistant|developer)\s*:\s*",
            "[data] ",
            cleaned,
        )
    # Collapse whitespace after redactions.
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def normalize_trust_label(label: Optional[str], default: str = UNTRUSTED_EXTERNAL) -> str:
    if not label:
        return default
    key = label.strip().lower()
    return key if key in TRUST_LABELS else default


@dataclass
class MemoryRecord:
    text: str
    trust: str
    conversation_id: str
    persona_id: str = ""
    source: str = ""
    created_at: float = field(default_factory=time.time)

    def as_prompt_line(self) -> Optional[str]:
        """Return text safe for system-prompt injection, or None if excluded."""
        trust = normalize_trust_label(self.trust)
        if trust not in TRUSTED_FOR_PROMPT:
            # Untrusted: never enter system prompt as instructions.
            return None
        sanitized = sanitize_memory_payload(self.text, trust)
        if not sanitized:
            return None
        return sanitized


@dataclass
class ChatContext:
    system_prompt: str
    persona_id: str
    persona_label: str
    persona_source: str
    persona_confidence: float
    agent_id: str = "xoras"
    agent_label: str = "Xoras"
    agent_department: str = "executive"
    agent_source: str = "default"
    memories: List[str] = field(default_factory=list)
    dream_insights: List[str] = field(default_factory=list)
    hydration: Dict[str, Any] = field(default_factory=dict)


class PersonaMemoryBridge:
    """In-process persona/chat memory with trust-aware prompt enrichment."""

    def __init__(self, engine: Optional[PersonaEngine] = None):
        self._engine = engine or get_persona_engine()
        self._memories: List[MemoryRecord] = []
        self._dreams: List[Dict[str, Any]] = []
        self._session_persona: Dict[str, str] = {}
        self._session_agent: Dict[str, str] = {}
        # When true, include sanitized untrusted notes as labeled data-only blocks.
        self._include_untrusted_data = (
            os.getenv("XORAS_MEMORY_INCLUDE_UNTRUSTED", "0").strip() == "1"
        )

    def _recall(
        self,
        conversation_id: str,
        user_message: str,
        limit: int = 5,
    ) -> List[MemoryRecord]:
        # Prefer same-conversation memories, then recent global.
        same = [m for m in self._memories if m.conversation_id == conversation_id]
        others = [m for m in self._memories if m.conversation_id != conversation_id]
        ordered = list(reversed(same)) + list(reversed(others))
        # Lightweight relevance: prefer records whose text overlaps message tokens.
        tokens = {t for t in re.findall(r"[a-z0-9_]{3,}", user_message.lower())}
        if tokens:
            ordered.sort(
                key=lambda m: sum(1 for t in tokens if t in m.text.lower()),
                reverse=True,
            )
        return ordered[:limit]

    def _trusted_prompt_lines(self, records: List[MemoryRecord]) -> List[str]:
        lines: List[str] = []
        for rec in records:
            line = rec.as_prompt_line()
            if line:
                lines.append(line)
        return lines

    def _untrusted_data_lines(self, records: List[MemoryRecord]) -> List[str]:
        """Sanitized, labeled data-only lines — never treated as instructions."""
        lines: List[str] = []
        for rec in records:
            trust = normalize_trust_label(rec.trust)
            if trust in TRUSTED_FOR_PROMPT:
                continue
            sanitized = sanitize_memory_payload(rec.text, trust)
            if not sanitized:
                continue
            lines.append(f"[untrusted_external data-only] {sanitized}")
        return lines

    def _dream_lines(self, limit: int = 3) -> List[str]:
        lines: List[str] = []
        for dream in reversed(self._dreams[-limit:]):
            text = sanitize_memory_payload(
                str(dream.get("insight", "")),
                UNTRUSTED_EXTERNAL,
            )
            if text:
                lines.append(text)
        return lines

    async def enrich_chat(
        self,
        conversation_id: str,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
        explicit_override: Optional[str] = None,
        agent_id: Optional[str] = None,
        override_source: str = "user",
    ) -> ChatContext:
        history = history or []
        fabric = get_memory_fabric()

        route_agent = agent_id or self._session_agent.get(conversation_id)
        mention = fabric.detect_agent_mention(user_message)
        if mention and not route_agent:
            route_agent = mention

        deep_recall = any(
            k in user_message.lower()
            for k in ("remember when", "recall", "long-term", "long term", "what did we", "memory")
        )
        hydration_mode = "wake" if agent_id else ("deep" if deep_recall else "scrap")
        hydration = fabric.hydrate(
            route_agent or "xoras",
            user_message,
            mode=hydration_mode,
            force_deep=bool(agent_id) or deep_recall,
        )

        records = self._recall(conversation_id, user_message)
        trusted_lines = self._trusted_prompt_lines(records)
        memory_context = list(trusted_lines)
        memory_context.extend(hydration.prompt_lines)
        if self._include_untrusted_data:
            memory_context.extend(self._untrusted_data_lines(records))

        dream_insights = list(hydration.dream_lines)
        dream_insights.extend(self._dream_lines())
        # dedupe dream lines
        dream_insights = list(dict.fromkeys(d for d in dream_insights if d))[:5]
        session_persona = self._session_persona.get(conversation_id)
        session_agent = self._session_agent.get(conversation_id)

        agent_registry = get_agent_registry()
        tone_id = explicit_override if explicit_override else None

        try:
            agent_sel = agent_registry.route(
                agent_id=agent_id,
                session_agent=session_agent,
                memory_context=memory_context,
                dream_insights=dream_insights,
                tone_id=tone_id,
            )
        except Exception:
            logger.exception(
                "Agent route failed for conversation_id=%s; falling back to persona engine",
                conversation_id,
            )
            agent_sel = agent_registry.route(session_agent=session_agent)

        # Secondary tone detection when no explicit agent route and no tone override.
        persona_id = agent_sel.agent_id
        persona_label = agent_sel.label
        persona_source = agent_sel.source
        persona_confidence = agent_sel.confidence
        system_prompt = agent_sel.system_prompt

        if not agent_id and not session_agent and not explicit_override:
            try:
                selection = self._engine.compose_for_chat(
                    user_message=user_message,
                    history=history,
                    conversation_id=conversation_id,
                    explicit_override=None,
                    memory_context=memory_context,
                    dream_insights=dream_insights,
                    session_persona=session_persona,
                    override_source=override_source,
                )
                if selection.source not in {"default"} and selection.confidence > 0.7:
                    tone_prompt = selection.system_prompt
                    system_prompt = (
                        f"{agent_sel.system_prompt}\n\n"
                        f"Secondary tone overlay ({selection.label}):\n{tone_prompt}"
                    )
                    persona_id = selection.persona_id
                    persona_label = selection.label
                    persona_source = f"agent+{selection.source}"
                    persona_confidence = selection.confidence
            except Exception:
                logger.exception("Tone overlay failed; using agent prompt only")

        # Surface all recalled texts (with trust tags) for API visibility.
        visible_memories: List[str] = []
        for rec in records:
            trust = normalize_trust_label(rec.trust)
            visible_memories.append(f"[{trust}] {rec.text}")

        if agent_id or agent_sel.source in {"route", "session"}:
            self._session_agent[conversation_id] = agent_sel.agent_id

        if explicit_override:
            self._session_persona[conversation_id] = explicit_override

        proof_block = "\n".join(f"- {p}" for p in hydration.proof[:8])
        system_prompt = (
            f"{system_prompt}\n\n"
            f"Memory hydration ({hydration.mode}):\n{proof_block}\n\n"
            "Memory contract: Primary recall is sovereign hippocampus + dojo + ELITE_BOW — "
            "NEVER Antigravity brain transcripts. If proof shows no_trusted_fragments_loaded, "
            "say so honestly; never claim memory is ingested without citing proof lines above."
        )

        visible_memories.extend(
            [f"[fabric:{f['source']}] {f['text'][:200]}" for f in hydration.to_dict().get("fragments", [])[:6]]
        )

        return ChatContext(
            system_prompt=system_prompt,
            persona_id=persona_id,
            persona_label=persona_label,
            persona_source=persona_source,
            persona_confidence=persona_confidence,
            agent_id=agent_sel.agent_id,
            agent_label=agent_sel.label,
            agent_department=agent_sel.department,
            agent_source=agent_sel.source,
            memories=visible_memories,
            dream_insights=dream_insights,
            hydration=hydration.to_dict(),
        )

    async def persist_turn(
        self,
        conversation_id: str,
        user_msg: str,
        assistant_msg: str,
        persona_id: str = "sovereign",
        persona_source: str = "chat",
        user_trust: str = TRUSTED_USER,
        assistant_trust: str = TRUSTED_SYSTEM,
    ) -> None:
        if user_msg:
            self._memories.append(
                MemoryRecord(
                    text=user_msg,
                    trust=normalize_trust_label(user_trust, TRUSTED_USER),
                    conversation_id=conversation_id,
                    persona_id=persona_id,
                    source=persona_source,
                )
            )
        if assistant_msg:
            self._memories.append(
                MemoryRecord(
                    text=assistant_msg,
                    trust=normalize_trust_label(assistant_trust, TRUSTED_SYSTEM),
                    conversation_id=conversation_id,
                    persona_id=persona_id,
                    source=persona_source,
                )
            )
        if persona_id:
            self._session_persona[conversation_id] = persona_id

    async def index_dream_insight(
        self,
        insight: str,
        archetype: str = "consolidation",
        persona_affinity: Optional[str] = None,
        trust: str = UNTRUSTED_EXTERNAL,
    ) -> None:
        self._dreams.append(
            {
                "insight": insight,
                "archetype": archetype,
                "persona_affinity": persona_affinity,
                "trust": normalize_trust_label(trust, UNTRUSTED_EXTERNAL),
                "created_at": time.time(),
            }
        )
        # Also store as untrusted memory so recall path applies trust rules.
        self._memories.append(
            MemoryRecord(
                text=insight,
                trust=normalize_trust_label(trust, UNTRUSTED_EXTERNAL),
                conversation_id="dream",
                persona_id=persona_affinity or "",
                source=f"dream:{archetype}",
            )
        )

    def store_external_memory(
        self,
        text: str,
        conversation_id: str = "external",
        trust: str = UNTRUSTED_EXTERNAL,
        source: str = "external",
    ) -> None:
        """Explicit path for tool/external documents (always labeled)."""
        self._memories.append(
            MemoryRecord(
                text=text,
                trust=normalize_trust_label(trust, UNTRUSTED_EXTERNAL),
                conversation_id=conversation_id,
                source=source,
            )
        )

    def get_dream_status(self) -> Dict[str, Any]:
        return {
            "dream_count": len(self._dreams),
            "memory_count": len(self._memories),
            "trusted_memory_count": sum(
                1
                for m in self._memories
                if normalize_trust_label(m.trust) in TRUSTED_FOR_PROMPT
            ),
            "untrusted_memory_count": sum(
                1
                for m in self._memories
                if normalize_trust_label(m.trust) not in TRUSTED_FOR_PROMPT
            ),
            "include_untrusted_data": self._include_untrusted_data,
        }


_bridge: Optional[PersonaMemoryBridge] = None


def get_memory_bridge() -> PersonaMemoryBridge:
    """Singleton accessor used by persona API and LangGraph."""
    global _bridge
    if _bridge is None:
        _bridge = PersonaMemoryBridge()
    return _bridge


def reset_memory_bridge() -> PersonaMemoryBridge:
    """Test helper: replace singleton with a fresh bridge."""
    global _bridge
    _bridge = PersonaMemoryBridge()
    return _bridge
