"""FastAPI sidecar for persona composition and memory bridge."""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from fastapi import FastAPI
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    FastAPI = None  # type: ignore

from xoras_agent_registry import get_agent_registry
from xoras_memory_fabric import get_memory_fabric
from xoras_persona_memory_bridge import get_memory_bridge
from xoras_persona_engine import get_persona_engine


if FastAPI is not None:
    app = FastAPI(title="Xoras Persona API", version="1.0.0")

    class ComposeRequest(BaseModel):
        conversation_id: str = "default"
        user_message: str
        history: List[Dict[str, str]] = []
        explicit_override: Optional[str] = None
        agent_id: Optional[str] = None
        override_source: str = "user"

    class PersistRequest(BaseModel):
        conversation_id: str
        user_message: str
        assistant_message: str
        persona_id: str = "sovereign"
        persona_source: str = "chat"

    class DreamInsightRequest(BaseModel):
        insight: str
        archetype: str = "consolidation"
        persona_affinity: Optional[str] = None

    class WakeRequest(BaseModel):
        agent_id: str = "xoras"
        conversation_id: str = "wake"
        user_message: str = "WAKE ROUTE ingest memory"

    class HydrateRequest(BaseModel):
        agent_id: str = "xoras"
        query: str = ""
        mode: str = "scrap"
        force_deep: bool = False

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "xoras-persona-api"}

    @app.get("/personas")
    async def list_personas():
        engine = get_persona_engine()
        return {"personas": engine.list_personas()}

    @app.get("/agents")
    async def list_agents():
        registry = get_agent_registry()
        return {
            "agents": registry.list_agents(),
            "departments": registry.list_departments(),
            "default_agent": registry.default_agent,
        }

    @app.post("/persona/compose")
    async def compose_persona(req: ComposeRequest):
        bridge = get_memory_bridge()
        ctx = await bridge.enrich_chat(
            conversation_id=req.conversation_id,
            user_message=req.user_message,
            history=req.history,
            explicit_override=req.explicit_override,
            agent_id=req.agent_id,
            override_source=req.override_source,
        )
        return {
            "system_prompt": ctx.system_prompt,
            "persona_id": ctx.persona_id,
            "persona_label": ctx.persona_label,
            "persona_source": ctx.persona_source,
            "persona_confidence": ctx.persona_confidence,
            "agent_id": ctx.agent_id,
            "agent_label": ctx.agent_label,
            "agent_department": ctx.agent_department,
            "agent_source": ctx.agent_source,
            "memories": ctx.memories,
            "dream_insights": ctx.dream_insights,
            "hydration": ctx.hydration,
        }

    @app.post("/memory/enrich")
    async def enrich_memory(req: ComposeRequest):
        return await compose_persona(req)

    @app.post("/memory/persist")
    async def persist_memory(req: PersistRequest):
        bridge = get_memory_bridge()
        await bridge.persist_turn(
            conversation_id=req.conversation_id,
            user_msg=req.user_message,
            assistant_msg=req.assistant_message,
            persona_id=req.persona_id,
            persona_source=req.persona_source,
        )
        return {"status": "ok"}

    @app.post("/memory/dream")
    async def index_dream(req: DreamInsightRequest):
        bridge = get_memory_bridge()
        await bridge.index_dream_insight(
            insight=req.insight,
            archetype=req.archetype,
            persona_affinity=req.persona_affinity,
        )
        return {"status": "ok"}

    @app.get("/memory/status")
    async def memory_status():
        fabric = get_memory_fabric()
        bridge = get_memory_bridge()
        return {
            "fabric": fabric.status(),
            "bridge": bridge.get_dream_status(),
        }

    @app.post("/memory/hydrate")
    async def memory_hydrate(req: HydrateRequest):
        fabric = get_memory_fabric()
        result = fabric.hydrate(
            req.agent_id,
            req.query,
            mode=req.mode,
            force_deep=req.force_deep,
        )
        return result.to_dict()

    @app.post("/memory/wake")
    async def memory_wake(req: WakeRequest):
        """Agent wake with full memory hydration — proof returned, no theater."""
        fabric = get_memory_fabric()
        hydration = fabric.hydrate(req.agent_id, req.user_message, mode="wake", force_deep=True)
        bridge = get_memory_bridge()
        ctx = await bridge.enrich_chat(
            conversation_id=req.conversation_id,
            user_message=req.user_message,
            history=[],
            agent_id=req.agent_id,
            override_source="operator",
        )
        registry = get_agent_registry()
        agent = registry.load_agent(req.agent_id)
        return {
            "status": "awake",
            "agent_id": ctx.agent_id,
            "agent_label": ctx.agent_label,
            "hydration": hydration.to_dict(),
            "proof": hydration.proof,
            "speak_lines": [
                f"I am {ctx.agent_label}. Memory hydration loaded {len(hydration.fragments)} fragments.",
                f"Sources reached: {', '.join(hydration.sources_reached) or 'none'}.",
            ] + [f"Recall: {p}" for p in hydration.proof[:3]],
            "identity": agent.identity[:400] if agent else "",
            "forbidden": "Do not cite Antigravity brain as primary memory.",
        }

    @app.get("/dream/status")
    async def dream_status():
        bridge = get_memory_bridge()
        return bridge.get_dream_status()

else:
    app = None


def run_server(host: str = "127.0.0.1", port: int = 8787):
    if FastAPI is None:
        raise RuntimeError("fastapi and uvicorn required: pip install fastapi uvicorn")
    uvicorn.run(
        "xoras_persona_api:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    port = int(os.environ.get("XORAS_PERSONA_PORT", "8787"))
    run_server(port=port)
