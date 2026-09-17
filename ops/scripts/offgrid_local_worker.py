"""
Autonomous 24/7 Off-Grid Background Dispatcher
Dispatches all queue tasks, episode generation, YouTube publishing,
and continuous model training directly to installed local models (sovereign-hermes).
Zero cloud tokens burned. Pure bare-metal execution.
"""

import os
import sys
import json
import time
import urllib.request
import logging
import traceback
from datetime import datetime

SSOT_ROOT = os.environ.get(
    "SSOT_ROOT",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
)
LOG_DIR = os.path.join(SSOT_ROOT, "memory", "agent_logs")
OFFGRID_LOG = os.path.join(LOG_DIR, "offgrid_worker.log")
RECEIPTS_LOG = os.path.join(LOG_DIR, "offgrid_receipts.jsonl")
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
PRIMARY_MODEL = "sovereign-hermes"

os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=OFFGRID_LOG,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [OFFGRID-WORKER] %(message)s"
)
log = logging.getLogger("offgrid_worker")

def query_local_model(prompt: str, timeout: int = 180) -> str:
    payload = {
        "model": PRIMARY_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"num_ctx": 4096, "temperature": 0.3}
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
            body = json.loads(resp.read().decode("utf-8"))
            return body.get("response", "").strip()
    except Exception as e:
        log.error("Local inference error on %s: %s", PRIMARY_MODEL, e)
        return f"[LOCAL_INFERENCE_ERROR]: {e}"

def log_receipt(task_id: str, prompt: str, result: str):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "task_id": task_id,
        "model": PRIMARY_MODEL,
        "prompt_snippet": prompt[:150],
        "result_snippet": result[:200]
    }
    with open(RECEIPTS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def run_loop():
    log.info("Off-grid local model worker engaged on %s. All processing strictly local.", PRIMARY_MODEL)

    # 1. Run YouTube builder
    try:
        sys.path.insert(0, os.path.join(SSOT_ROOT, "ops", "publishing"))
        from sovereign_youtube_builder import SovereignYouTubeEngine
        engine = SovereignYouTubeEngine()
        ep = engine.generate_pilot_episode()
        log.info("Generated Episode 001: %s (SHA: %s)", ep["title"], ep["secured_assurance_sha256"][:10])
    except Exception as e:
        log.error("Failed to generate YouTube episode: %s", e)

    # 2. Continuous Task Loop
    cycle = 0
    while True:
        cycle += 1
        try:
            log.info("--- Continuous Off-Grid Cycle #%d ---", cycle)

            # Deepen autonomous episode content via local model
            prompt = (
                "You are Maxx and the Lead 9 Sovereign Council. Produce a detailed pedagogical technical lesson "
                "on eliminating memory walls in local LLM inference using hyperbolic geometric compression. "
                "Include code snippets, mathematical definitions, and Secured Assurance proofs."
            )
            response = query_local_model(prompt)
            log.info("Cycle #%d response generated (%d chars)", cycle, len(response))
            log_receipt(f"CYCLE-{cycle}-PEDAGOGY", prompt, response)

            # Check and run autonomy pulse
            try:
                sys.path.insert(0, os.path.join(SSOT_ROOT, "products", "xmars_os"))
                from autonomy import autonomy_engine
                from self_upgrade import self_upgrade_engine
                autonomy_engine.run_cycle(trigger="offgrid_worker")
                self_upgrade_engine.evaluate_and_evolve()
            except Exception as e:
                log.warning("Autonomy pulse warning: %s", e)

        except Exception as e:
            log.error("Cycle error: %s\n%s", e, traceback.format_exc())

        time.sleep(60)

if __name__ == "__main__":
    run_loop()
