"""Xoras Memory Fabric — unified hydration across sovereign, dojo, lex, mongo.

Agents must NOT cite Antigravity brain transcripts as primary memory.
This module is the canonical read path for wake / route / name-trigger recall.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from xoras_agent_registry import get_agent_registry
from xoras_persona_engine import sanitize_for_prompt

logger = logging.getLogger("XorasMemoryFabric")

TRUSTED_SYSTEM = "trusted_system"
TRUSTED_USER = "trusted_user"
UNTRUSTED_EXTERNAL = "untrusted_external"

# ── Canonical paths (override via env) ─────────────────────────────────────
HIPPOCAMPUS = Path(
    os.getenv("XORAS_HIPPOCAMPUS", str(Path.home() / ".sovereign" / "hippocampus"))
)
DREAM_DB = Path(os.getenv("XORAS_DREAM_DB", str(HIPPOCAMPUS / "dream.db")))
EPISODIC_DB = Path(os.getenv("XORAS_EPISODIC_DB", str(HIPPOCAMPUS / "episodic.db")))
SEMANTIC_DB = Path(os.getenv("XORAS_SEMANTIC_DB", str(HIPPOCAMPUS / "semantic.db")))
OPS_MEMORY_DB = Path(os.getenv("XORAS_OPS_MEMORY_DB", str(HIPPOCAMPUS / "xoras_memory.db")))
DOJO_DB = Path(
    os.getenv(
        "XORAS_DOJO_DB",
        str(
            Path.home()
            / "Desktop/Xoras_Workspace/AI_Core/Xoras_Project/xoras-core/Omni_Dojo_Sandbox/Error_Catalyst/global_catalyst.db"
        ),
    )
)
WISDOM_DIR = Path(
    os.getenv(
        "XORAS_WISDOM_DIR",
        str(
            Path.home()
            / "Desktop/Xoras_Workspace/AI_Core/Xoras_Project/xoras-core/Omni_Dojo_Sandbox/Wisdom_Archives"
        ),
    )
)
HYDRATION_LOG = Path(os.getenv("XORAS_HYDRATION_LOG", str(HIPPOCAMPUS / "hydration_audit.jsonl")))
LEX_CORE_URL = os.getenv("LEX_CORE_URL", "http://127.0.0.1:28282").rstrip("/")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

BLOCKED_SOURCE_PREFIXES = (
    ".gemini/antigravity/brain",
    "antigravity/brain",
)

PRIMARY_AGENTS = (
    "xoras", "maxx", "zorex", "orion", "jarvis", "axlon",
    "clara", "evan", "arelius", "dr_jeremy",
)


@dataclass
class MemoryFragment:
    text: str
    source: str
    trust: str
    agent_affinity: Optional[str] = None
    score: float = 0.5
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text[:500],
            "source": self.source,
            "trust": self.trust,
            "agent_affinity": self.agent_affinity,
            "score": round(self.score, 3),
            "timestamp": self.timestamp,
        }


@dataclass
class HydrationResult:
    agent_id: str
    mode: str  # scrap | deep | wake
    fragments: List[MemoryFragment] = field(default_factory=list)
    sources_reached: List[str] = field(default_factory=list)
    sources_failed: List[str] = field(default_factory=list)
    prompt_lines: List[str] = field(default_factory=list)
    dream_lines: List[str] = field(default_factory=list)
    proof: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "mode": self.mode,
            "fragment_count": len(self.fragments),
            "sources_reached": self.sources_reached,
            "sources_failed": self.sources_failed,
            "proof": self.proof,
            "fragments": [f.to_dict() for f in self.fragments[:20]],
        }


def _tokens(text: str) -> Set[str]:
    return {t for t in re.findall(r"[a-z0-9_]{3,}", (text or "").lower())}


def _score_text(text: str, query_tokens: Set[str]) -> float:
    if not text or not query_tokens:
        return 0.1
    lower = text.lower()
    hits = sum(1 for t in query_tokens if t in lower)
    return min(1.0, 0.15 + hits * 0.12)


def _sqlite_query(db_path: Path, sql: str, params: tuple = ()) -> List[tuple]:
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception as exc:
        logger.debug("SQLite read failed %s: %s", db_path.name, exc)
        return []


class MemoryFabric:
    """Multi-source memory loader with agent affinity and trust tiers."""

    def __init__(self) -> None:
        self._agent_names = self._build_agent_aliases()

    def _build_agent_aliases(self) -> Dict[str, str]:
        aliases: Dict[str, str] = {}
        try:
            for agent in get_agent_registry().list_agents():
                aid = agent["id"]
                aliases[aid] = aid
                aliases[aid.replace("_", " ")] = aid
                aliases[aid.replace("_", "")] = aid
                name = agent.get("name", "").lower()
                if name:
                    aliases[name] = aid
        except Exception:
            for aid in PRIMARY_AGENTS:
                aliases[aid] = aid
        return aliases

    def detect_agent_mention(self, text: str) -> Optional[str]:
        lower = (text or "").lower()
        for alias, aid in sorted(self._agent_names.items(), key=lambda x: -len(x[0])):
            if len(alias) < 3:
                continue
            if re.search(rf"\b{re.escape(alias)}\b", lower):
                return aid
        if re.search(r"(?i)\bwake\s+route\s+(\w+)", text or ""):
            m = re.search(r"(?i)\bwake\s+route\s+(\w+)", text)
            if m:
                key = m.group(1).lower().replace("-", "_")
                return self._agent_names.get(key, key)
        if re.search(r"(?i)/route\s+(\w+)", text or ""):
            m = re.search(r"(?i)/route\s+(\w+)", text)
            if m:
                key = m.group(1).lower().replace("-", "_")
                return self._agent_names.get(key, key)
        return None

    def _is_blocked_source(self, source: str) -> bool:
        s = source.lower()
        return any(b in s for b in BLOCKED_SOURCE_PREFIXES)

    def _from_dreams(self, agent_id: str, query_tokens: Set[str], limit: int) -> List[MemoryFragment]:
        rows = _sqlite_query(
            DREAM_DB,
            "SELECT timestamp, content, insights FROM dreams ORDER BY rowid DESC LIMIT ?",
            (limit * 3,),
        )
        frags: List[MemoryFragment] = []
        for ts, content, insights in rows:
            blob = " ".join(filter(None, [content or "", insights or ""]))
            if not blob.strip():
                continue
            score = _score_text(blob, query_tokens)
            frags.append(
                MemoryFragment(
                    text=sanitize_for_prompt(blob[:800]),
                    source="sovereign_dream",
                    trust=TRUSTED_SYSTEM,
                    agent_affinity=agent_id,
                    score=score,
                    timestamp=str(ts),
                )
            )
        frags.sort(key=lambda f: f.score, reverse=True)
        return frags[:limit]

    def _from_episodic(self, query_tokens: Set[str], limit: int) -> List[MemoryFragment]:
        rows = _sqlite_query(
            EPISODIC_DB,
            """SELECT timestamp, situation, action, result, lessons, tags
               FROM episodes ORDER BY rowid DESC LIMIT ?""",
            (limit * 2,),
        )
        frags: List[MemoryFragment] = []
        for ts, situation, action, result, lessons, tags in rows:
            blob = " | ".join(filter(None, [situation, action, result, lessons, tags]))
            if not blob.strip():
                continue
            frags.append(
                MemoryFragment(
                    text=sanitize_for_prompt(blob[:600]),
                    source="sovereign_episodic",
                    trust=TRUSTED_SYSTEM,
                    score=_score_text(blob, query_tokens),
                    timestamp=str(ts),
                )
            )
        frags.sort(key=lambda f: f.score, reverse=True)
        return frags[:limit]

    def _from_semantic(self, query_tokens: Set[str], limit: int) -> List[MemoryFragment]:
        rows = _sqlite_query(
            SEMANTIC_DB,
            "SELECT label, type, properties, updated_at FROM nodes ORDER BY updated_at DESC LIMIT ?",
            (limit * 2,),
        )
        frags: List[MemoryFragment] = []
        for label, typ, props, updated in rows:
            blob = f"{label} ({typ}): {props or ''}"
            frags.append(
                MemoryFragment(
                    text=sanitize_for_prompt(blob[:500]),
                    source="sovereign_semantic",
                    trust=TRUSTED_SYSTEM,
                    score=_score_text(blob, query_tokens),
                    timestamp=str(updated),
                )
            )
        frags.sort(key=lambda f: f.score, reverse=True)
        return frags[:limit]

    def _from_dojo(self, query_tokens: Set[str], limit: int) -> List[MemoryFragment]:
        rows = _sqlite_query(
            DOJO_DB,
            """SELECT timestamp, exception_type, error_message, healing_action
               FROM error_logs
               WHERE status IN ('HEALED', 'ARCHIVED')
               ORDER BY id DESC LIMIT ?""",
            (limit * 2,),
        )
        frags: List[MemoryFragment] = []
        for ts, exc, err, heal in rows:
            blob = f"[{exc}] {err} → healed: {heal}"
            frags.append(
                MemoryFragment(
                    text=sanitize_for_prompt(blob[:600]),
                    source="dojo_catalyst",
                    trust=TRUSTED_SYSTEM,
                    score=_score_text(blob, query_tokens),
                    timestamp=str(ts),
                )
            )
        return frags[:limit]

    def _from_wisdom_files(self, query_tokens: Set[str], limit: int) -> List[MemoryFragment]:
        if not WISDOM_DIR.exists():
            return []
        files = sorted(WISDOM_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        frags: List[MemoryFragment] = []
        for path in files[: limit * 2]:
            try:
                raw = path.read_text(encoding="utf-8", errors="replace")[:1200]
            except OSError:
                continue
            score = _score_text(raw, query_tokens)
            if score < 0.2 and query_tokens:
                continue
            frags.append(
                MemoryFragment(
                    text=sanitize_for_prompt(
                        f"{path.stem}: {raw[:400]}", TRUSTED_SYSTEM
                    ),
                    source="dojo_wisdom",
                    trust=TRUSTED_SYSTEM,
                    score=score,
                    timestamp=str(path.stat().st_mtime),
                )
            )
        frags.sort(key=lambda f: f.score, reverse=True)
        return frags[:limit]

    def _from_ops_incidents(self, limit: int) -> List[MemoryFragment]:
        rows = _sqlite_query(
            OPS_MEMORY_DB,
            """SELECT logged_at, filepath, error_type, error_details
               FROM daemon_incidents ORDER BY id DESC LIMIT ?""",
            (limit,),
        )
        if rows:
            return [
                MemoryFragment(
                    text=sanitize_for_prompt(
                        f"[{r[2]}] {r[1]}: {r[3][:200]}", UNTRUSTED_EXTERNAL
                    ),
                    source="sovereign_ops_incidents",
                    trust=UNTRUSTED_EXTERNAL,
                    score=0.3,
                    timestamp=str(r[0]),
                )
                for r in rows
            ]
        rows = _sqlite_query(
            OPS_MEMORY_DB,
            "SELECT path, hash FROM file_registry ORDER BY rowid DESC LIMIT ?",
            (limit,),
        )
        return [
            MemoryFragment(
                text=sanitize_for_prompt(f"Registry: {r[0]} ({r[1]})"),
                source="sovereign_ops_registry",
                trust=UNTRUSTED_EXTERNAL,
                score=0.2,
            )
            for r in rows
        ]

    def _from_lex_core(self, agent_id: str, query: str) -> Optional[MemoryFragment]:
        try:
            health_req = urllib.request.Request(f"{LEX_CORE_URL}/health", method="GET")
            with urllib.request.urlopen(health_req, timeout=1.5) as resp:
                if resp.status != 200:
                    return None
        except (urllib.error.URLError, TimeoutError, OSError):
            return None

        payload = json.dumps(
            {
                "query": f"Recall context for agent {agent_id}: {query[:300]}",
                "context": {"agent_id": agent_id, "mode": "memory_scrap"},
            }
        ).encode()
        try:
            req = urllib.request.Request(
                f"{LEX_CORE_URL}/query",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=4) as resp:
                body = json.loads(resp.read().decode())
            answer = body.get("response") or body.get("answer") or ""
            if not answer:
                return None
            return MemoryFragment(
                text=sanitize_for_prompt(str(answer)[:700]),
                source="lex_core",
                trust=TRUSTED_USER,
                agent_affinity=agent_id,
                score=0.85,
            )
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            logger.debug("Lex_Core unavailable: %s", exc)
            return None

    def _from_mongo(self, agent_id: str, query_tokens: Set[str], limit: int) -> List[MemoryFragment]:
        try:
            from pymongo import MongoClient  # type: ignore
        except ImportError:
            return []

        frags: List[MemoryFragment] = []
        try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=800)
            db = client.get_default_database() if "/" in MONGO_URI.split("localhost")[-1] else client.xoras_db
            for coll_name in ("memories", "episodes", "agent_memory"):
                if coll_name not in db.list_collection_names():
                    continue
                coll = db[coll_name]
                cursor = coll.find(
                    {"$or": [{"agent_id": agent_id}, {"persona_affinity": agent_id}]},
                    limit=limit,
                ).sort("_id", -1)
                for doc in cursor:
                    text = doc.get("text") or doc.get("content") or doc.get("insight") or ""
                    if not text:
                        continue
                    frags.append(
                        MemoryFragment(
                            text=sanitize_for_prompt(str(text)[:600]),
                            source=f"mongo:{coll_name}",
                            trust=TRUSTED_USER,
                            agent_affinity=agent_id,
                            score=_score_text(str(text), query_tokens),
                        )
                    )
            client.close()
        except Exception as exc:
            logger.debug("Mongo memory skip: %s", exc)
        return frags[:limit]

    def _audit_log(self, result: HydrationResult) -> None:
        try:
            HYDRATION_LOG.parent.mkdir(parents=True, exist_ok=True)
            line = json.dumps({"ts": time.time(), **result.to_dict()}) + "\n"
            with open(HYDRATION_LOG, "a", encoding="utf-8") as f:
                f.write(line)
        except OSError:
            pass

    def hydrate(
        self,
        agent_id: str,
        query: str = "",
        mode: str = "scrap",
        force_deep: bool = False,
    ) -> HydrationResult:
        """Load memory scrap (fast) or deep recall (token-ranked across sources)."""
        registry = get_agent_registry()
        resolved = registry._resolve_agent_id(agent_id) or agent_id or "xoras"

        mention = self.detect_agent_mention(query)
        if mention and not force_deep:
            resolved = mention

        deep = force_deep or mode == "deep" or mode == "wake"
        if any(k in (query or "").lower() for k in ("remember when", "recall", "what did we", "long-term", "long term")):
            deep = True

        per_source = 4 if deep else 2
        tokens = _tokens(query) | _tokens(resolved)
        result = HydrationResult(agent_id=resolved, mode="deep" if deep else "scrap")

        loaders: List[Tuple[str, Any]] = [
            ("sovereign_dream", lambda: self._from_dreams(resolved, tokens, per_source)),
            ("sovereign_episodic", lambda: self._from_episodic(tokens, per_source)),
            ("sovereign_semantic", lambda: self._from_semantic(tokens, per_source)),
            ("dojo_catalyst", lambda: self._from_dojo(tokens, per_source)),
            ("dojo_wisdom", lambda: self._from_wisdom_files(tokens, per_source)),
            ("sovereign_ops", lambda: self._from_ops_incidents(2 if deep else 1)),
        ]

        if deep:
            loaders.append(("mongo", lambda: self._from_mongo(resolved, tokens, per_source)))
            lex = self._from_lex_core(resolved, query)
            if lex:
                result.fragments.append(lex)
                result.sources_reached.append("lex_core")

        for name, loader in loaders:
            try:
                frags = loader()
                if frags:
                    result.fragments.extend(frags)
                    result.sources_reached.append(name)
                else:
                    result.sources_failed.append(f"{name}:empty")
            except Exception as exc:
                result.sources_failed.append(f"{name}:{exc}")

        # Rank and dedupe
        seen: Set[str] = set()
        ranked: List[MemoryFragment] = []
        for frag in sorted(result.fragments, key=lambda f: f.score, reverse=True):
            if self._is_blocked_source(frag.source):
                continue
            key = frag.text[:120]
            if key in seen:
                continue
            seen.add(key)
            ranked.append(frag)

        cap = 12 if deep else 6
        result.fragments = ranked[:cap]

        for frag in result.fragments:
            if frag.trust in (TRUSTED_SYSTEM, TRUSTED_USER) and frag.text:
                line = f"[{frag.source}] {frag.text}"
                result.prompt_lines.append(line)
                if frag.source == "sovereign_dream":
                    result.dream_lines.append(frag.text[:300])
                result.proof.append(
                    f"{frag.source} · score={frag.score:.2f}"
                    + (f" · {frag.timestamp}" if frag.timestamp else "")
                )

        if not result.proof:
            result.proof.append("no_trusted_fragments_loaded — do not claim memory is ingested")

        self._audit_log(result)
        return result

    def status(self) -> Dict[str, Any]:
        return {
            "hippocampus": str(HIPPOCAMPUS),
            "dream_db": DREAM_DB.exists(),
            "dream_count": len(_sqlite_query(DREAM_DB, "SELECT id FROM dreams LIMIT 500")),
            "episodic_db": EPISODIC_DB.exists(),
            "semantic_db": SEMANTIC_DB.exists(),
            "dojo_db": DOJO_DB.exists(),
            "wisdom_dir": WISDOM_DIR.exists(),
            "wisdom_files": len(list(WISDOM_DIR.glob("*.md"))) if WISDOM_DIR.exists() else 0,
            "lex_core_url": LEX_CORE_URL,
            "mongo_uri": MONGO_URI.split("@")[-1],  # hide creds
            "blocked_sources": list(BLOCKED_SOURCE_PREFIXES),
            "hydration_log": str(HYDRATION_LOG),
        }


_fabric: Optional[MemoryFabric] = None


def get_memory_fabric() -> MemoryFabric:
    global _fabric
    if _fabric is None:
        _fabric = MemoryFabric()
    return _fabric
