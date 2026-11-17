"""
Model Orchestrator — XORAS Sovereign OS
Routes incoming tasks, natural language inputs, and audio transcripts
to local on-machine models via Ollama.
Primary Model: sovereign-hermes
Fallback Models: deepseek-r1:1.5b, hermes3:8b, qwen2.5:1.5b, llama3.2
Completely off-grid. Zero cloud API dependencies.
"""

import os
import sys
import json
import time
import uuid
import urllib.request
import urllib.error
import logging
from typing import Dict, Any
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ModelOrchestrator] %(message)s"
)
log = logging.getLogger("model_orchestrator")

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")

# Load SSOT project context injection
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTEXT_FILE = PROJECT_ROOT / "agents" / "project_context_injection.md"
PROJECT_CONTEXT = ""
if CONTEXT_FILE.exists():
    with open(CONTEXT_FILE, "r") as f:
        PROJECT_CONTEXT = f.read()
else:
    log.warning("Project context injection file not found at %s", CONTEXT_FILE)

# Initialize DART DB
try:
    sys.path.insert(0, str(PROJECT_ROOT))
    from core.memory.dart_ring_buffer import DartMemoryManager
    dart_db = DartMemoryManager(capacity=4096)
    DART_DB_ACTIVE = True
    log.info("Dart DB online at %s (write_ptr=%s)", 
             PROJECT_ROOT / "memory" / "tri_brain" / "dart_db",
             dart_db.total_writes)
except Exception as e:
    dart_db = None
    DART_DB_ACTIVE = False
    log.warning("DART DB initialization failed (degraded mode): %s", e)

MODEL_REGISTRY = {
    'sovereign-hermes': {
        'capabilities': ['reasoning', 'code_generation', 'planning', 'orchestration', 'general'],
        'context_len': 4096,
        'temperature': 0.3
    },
    'deepseek-r1:1.5b': {
        'capabilities': ['verification', 'linting', 'status_checks', 'quick_commands'],
        'context_len': 4096,
        'temperature': 0.2
    },
    'hermes3:8b': {
        'capabilities': ['fallback_reasoning', 'code_review'],
        'context_len': 4096,
        'temperature': 0.3
    },
    'qwen2.5:1.5b': {
        'capabilities': ['summarization', 'lightweight_queries'],
        'context_len': 4096,
        'temperature': 0.3
    },
    'llama3.2': {
        'capabilities': ['general_chat', 'brainstorming'],
        'context_len': 4096,
        'temperature': 0.5
    }
}

DEFAULT_PRIMARY_MODEL = 'sovereign-hermes'
DEFAULT_FALLBACK_MODEL = 'hermes3:8b'

INTENT_MAP = {
    'edit_file': 'sovereign-hermes',
    'code_gen': 'sovereign-hermes',
    'planning': 'sovereign-hermes',
    'verify': 'deepseek-r1:1.5b',
    'status': 'deepseek-r1:1.5b',
    'summarize': 'qwen2.5:1.5b',
    'chat': 'sovereign-hermes'
}

def select_model(intent: str) -> str:
    """Select appropriate local model for given intent, defaulting to sovereign-hermes."""
    return INTENT_MAP.get(intent, DEFAULT_PRIMARY_MODEL)

def dispatch(model_name: str, prompt: str, timeout: int = 120, agent_name: str = None) -> str:
    """Send prompt to local Ollama instance via HTTP POST and return generated text.
    Automatically injects SSOT project context to ensure agents stay loyal to project doctrine.
    """
    # Inject project context + agent SOUL if available
    context_prefix = PROJECT_CONTEXT
    if agent_name:
        agent_soul_path = PROJECT_ROOT / "agents" / "citizens" / agent_name / "SOUL.md"
        if agent_soul_path.exists():
            try:
                with open(agent_soul_path, "r") as f:
                    agent_soul = f.read()
                    context_prefix += f"\n\n### Agent-Specific Identity Override\n{agent_soul}"
            except Exception as e:
                log.warning("Failed to load SOUL for %s: %s", agent_name, e)
    
    # Prepend context to user prompt
    full_prompt = f"{context_prefix}\n\n### User Task\n{prompt}"
    
    payload = {
        "model": model_name,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "num_ctx": MODEL_REGISTRY.get(model_name, {}).get("context_len", 4096),
            "temperature": MODEL_REGISTRY.get(model_name, {}).get("temperature", 0.3),
            "top_p": 0.9,
            "repeat_penalty": 1.0
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("response", "").strip()
    except Exception as e:
        log.error("Dispatch to %s failed: %s", model_name, e)
        if model_name != DEFAULT_FALLBACK_MODEL:
            log.info("Attempting fallback to %s", DEFAULT_FALLBACK_MODEL)
            return dispatch(DEFAULT_FALLBACK_MODEL, prompt, timeout=timeout)
        return f"[ORCHESTRATOR ERROR]: {e}"

def orchestrate(transcript: str, intent_hint: str = None, agent_name: str = None, upstream_agent: str = "user") -> Dict[str, Any]:
    """Route request through governance cascade and return certified receipt.
    
    Flow:
    1. Classify intent (Jarvis)
    2. Select agent and model
    3. Log to DART (retrospective)
    4. Dispatch to model (Ollama)
    5. Return certified receipt with request ID, model, agent, response, latency
    """
    
    request_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
    t0 = time.time()
    
    try:
        text = transcript.strip()
        words = text.lower().split()

        # Step 1: Classify intent
        if intent_hint:
            intent = intent_hint
        elif any(w in words for w in ['edit', 'fix', 'write', 'create', 'update', 'refactor', 'code']):
            intent = 'code_gen'
        elif any(w in words for w in ['verify', 'test', 'check', 'audit', 'lint']):
            intent = 'verify'
        elif any(w in words for w in ['summarize', 'brief', 'digest']):
            intent = 'summarize'
        else:
            intent = 'chat'

        chosen_model = select_model(intent)
        agent_name = agent_name or "COLLECTIVE"
        
        log.info("[%s] Routing [intent=%s, agent=%s] to model: %s", request_id, intent, agent_name, chosen_model)

        # Step 2: Dispatch to model
        response_text = dispatch(chosen_model, transcript, agent_name=agent_name)

        # Step 3: Log to DART
        if DART_DB_ACTIVE and dart_db is not None:
            try:
                dart_seq = dart_db.record(
                    agent_id=hash(agent_name) & 0xFFFF,
                    action_hash=hash(f"{agent_name}:{intent}:{request_id}") & 0xFFFFFFFF,
                    state_flags=0x03,
                    payload_data=response_text[:488].encode("utf-8", errors="replace")
                )
            except Exception as e:
                log.warning("[%s] DART logging failed: %s", request_id, e)
                dart_seq = None
        else:
            dart_seq = None

        # Step 4: Return certified receipt
        elapsed = time.time() - t0
        return {
            "success": True,
            "request_id": request_id,
            "intent": intent,
            "model": chosen_model,
            "agent": agent_name,
            "response": response_text,
            "latency_sec": round(elapsed, 3),
            "dart_sequence": dart_seq,
            "dart_db_active": DART_DB_ACTIVE,
            "upstream_agent": upstream_agent
        }
    
    except Exception as e:
        log.error("[%s] Orchestration failed: %s", request_id, e)
        return {
            "success": False,
            "request_id": request_id,
            "error": str(e),
            "dart_db_active": DART_DB_ACTIVE
        }

if __name__ == "__main__":
    test_prompt = "Hello Maxx, report current readiness of the sovereign local stack."
    print("Testing orchestrator with prompt:", test_prompt)
    receipt = orchestrate(test_prompt, agent_name="maxx")
    print("\n--- Model Receipt ---")
    print(json.dumps(receipt, indent=2))
