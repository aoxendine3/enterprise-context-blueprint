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
import urllib.request
import urllib.error
import logging
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ModelOrchestrator] %(message)s"
)
log = logging.getLogger("model_orchestrator")

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")

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

def dispatch(model_name: str, prompt: str, timeout: int = 120) -> str:
    """Send prompt to local Ollama instance via HTTP POST and return generated text."""
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_ctx": MODEL_REGISTRY.get(model_name, {}).get("context_len", 4096),
            "temperature": MODEL_REGISTRY.get(model_name, {}).get("temperature", 0.3)
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

def orchestrate(transcript: str, intent_hint: str = None) -> Dict[str, Any]:
    """Classify intent, route to designated local model, and return execution receipt."""
    text = transcript.strip()
    words = text.lower().split()

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
    log.info("Routing prompt [intent=%s] to local model: %s", intent, chosen_model)

    response_text = dispatch(chosen_model, transcript)

    return {
        "intent": intent,
        "model": chosen_model,
        "prompt": transcript,
        "response": response_text
    }

if __name__ == "__main__":
    test_prompt = "Hello Maxx, report current readiness of the sovereign local stack."
    print("Testing orchestrator with prompt:", test_prompt)
    receipt = orchestrate(test_prompt)
    print("\n--- Model Receipt ---")
    print(json.dumps(receipt, indent=2))
