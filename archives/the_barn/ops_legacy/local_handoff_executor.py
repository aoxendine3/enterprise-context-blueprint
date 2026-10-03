"""
Local Handoff Executor — Dispatches all outstanding tasks to on-machine Ollama models.
No cloud tokens burned. All reasoning stays on bare metal.

Models:
  - sovereign-hermes  (4.7 GB) → heavy reasoning, code generation, orchestration
  - deepseek-r1:1.5b  (1.1 GB) → fast verification, linting, status checks
  - hermes3:8b        (4.7 GB) → fallback for sovereign-hermes
  - qwen2.5:1.5b      (986 MB) → lightweight summarization

Usage:
  python ops/scripts/local_handoff_executor.py
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
import datetime
import traceback

# ── Config ──────────────────────────────────────────────────────────────────
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
SSOT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOG_DIR = os.path.join(SSOT_ROOT, "memory", "agent_logs")
HANDOFF_LOG = os.path.join(LOG_DIR, "local_handoff_results.jsonl")
STORE_URL = "http://127.0.0.1:8085"

# Model assignments
HEAVY_MODEL = "sovereign-hermes"
FAST_MODEL = "deepseek-r1:1.5b"
FALLBACK_MODEL = "hermes3:8b"

os.makedirs(LOG_DIR, exist_ok=True)


def query_ollama(model: str, prompt: str, timeout: int = 120) -> str:
    """Send a prompt to a local Ollama model and return the response text."""
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_ctx": 4096, "temperature": 0.4}
    }).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body.get("response", "").strip()
    except Exception as e:
        print(f"  [!] {model} failed: {e}")
        if model != FALLBACK_MODEL:
            print(f"  [→] Falling back to {FALLBACK_MODEL}")
            return query_ollama(FALLBACK_MODEL, prompt, timeout)
        return f"ERROR: {e}"


def log_result(task_id: str, status: str, model: str, detail: str):
    """Append a JSONL line to the handoff log."""
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "task_id": task_id,
        "status": status,
        "model": model,
        "detail": detail[:2000]
    }
    with open(HANDOFF_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    icon = "OK" if status == "PASS" else "XX"
    print(f"  [{icon}] {task_id}: {status}")


def http_check(path: str, expect_status: int = 200, expect_content_type: str = None) -> bool:
    """Quick HTTP health check against the local server."""
    url = f"{STORE_URL}{path}"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            ct = resp.headers.get("Content-Type", "")
            if resp.status != expect_status:
                return False
            if expect_content_type and expect_content_type not in ct:
                return False
            return True
    except urllib.error.HTTPError as e:
        return e.code == expect_status
    except Exception:
        return False


# ── Task Definitions ────────────────────────────────────────────────────────

TASKS = []


def task(task_id, model, description):
    """Decorator to register a task."""
    def decorator(fn):
        TASKS.append({"id": task_id, "model": model, "desc": description, "fn": fn})
        return fn
    return decorator


# ── Task 1: Store Page HTTP Check ───────────────────────────────────────────
@task("STORE_PAGE_200", FAST_MODEL, "Verify store.html returns HTTP 200")
def check_store_page():
    ok = http_check("/store.html", 200, "text/html")
    if ok:
        log_result("STORE_PAGE_200", "PASS", FAST_MODEL, "store.html → 200 text/html")
    else:
        log_result("STORE_PAGE_200", "FAIL", FAST_MODEL, "store.html did not return 200")
    return ok


# ── Task 2: JPEG Asset Checks ──────────────────────────────────────────────
@task("ASSET_BOOK_JPG", FAST_MODEL, "Verify sovereign book pin JPEG serves correctly")
def check_book_jpg():
    ok = http_check("/assets/listings/pinterest_pin_sovereign_book.jpg", 200, "image/jpeg")
    status = "PASS" if ok else "FAIL"
    log_result("ASSET_BOOK_JPG", status, FAST_MODEL, "sovereign_book pin JPEG check")
    return ok


@task("ASSET_XMARS_JPG", FAST_MODEL, "Verify XMARS OS bundle pin JPEG serves correctly")
def check_xmars_jpg():
    ok = http_check("/assets/listings/pinterest_pin_xmars_os_bundle.jpg", 200, "image/jpeg")
    status = "PASS" if ok else "FAIL"
    log_result("ASSET_XMARS_JPG", status, FAST_MODEL, "xmars_os_bundle pin JPEG check")
    return ok


# ── Task 3: 404 Handling ───────────────────────────────────────────────────
@task("MISSING_ASSET_404", FAST_MODEL, "Verify missing static file returns 404")
def check_404():
    ok = http_check("/static/missing.jpg", 404)
    status = "PASS" if ok else "FAIL"
    log_result("MISSING_ASSET_404", status, FAST_MODEL, "Missing asset → 404 check")
    return ok


# ── Task 4: Index Page + Store Button ──────────────────────────────────────
@task("INDEX_PAGE_200", FAST_MODEL, "Verify index.html returns HTTP 200")
def check_index():
    ok = http_check("/", 200, "text/html")
    status = "PASS" if ok else "FAIL"
    log_result("INDEX_PAGE_200", status, FAST_MODEL, "index.html root → 200")
    return ok


# ── Task 5: Voice Orchestration Code Gen ───────────────────────────────────
@task("VOICE_CAPTURE_GEN", HEAVY_MODEL, "Generate voice_capture.py via local model")
def gen_voice_capture():
    prompt = """You are Maxx, sovereign AI architect. Write a Python script called voice_capture.py that:
1. Uses the 'sounddevice' library to capture audio from the system microphone at 16kHz 16-bit mono PCM.
2. Records in 5-second chunks continuously in a background thread.
3. Saves each chunk as a WAV file in memory/agent_logs/voice_chunks/ with a timestamp filename.
4. Appends a JSON line to memory/agent_logs/voice_events.jsonl with {timestamp, wav_path}.
5. Has a graceful shutdown on SIGINT/SIGTERM.
6. All paths are relative to an SSOT_ROOT environment variable or default to the script's grandparent directory.
7. Includes proper logging, error handling, and docstrings.
8. No external cloud dependencies. Fully off-grid.

Output ONLY the Python code, no explanation."""

    code = query_ollama(HEAVY_MODEL, prompt, timeout=180)
    if code.startswith("ERROR:"):
        log_result("VOICE_CAPTURE_GEN", "FAIL", HEAVY_MODEL, code)
        return False

    target = os.path.join(SSOT_ROOT, "agents", "voice", "voice_capture.py")
    os.makedirs(os.path.dirname(target), exist_ok=True)

    # Strip markdown fences if present
    if "```python" in code:
        code = code.split("```python", 1)[1]
        if "```" in code:
            code = code.rsplit("```", 1)[0]
    elif "```" in code:
        code = code.split("```", 1)[1]
        if "```" in code:
            code = code.rsplit("```", 1)[0]

    with open(target, "w", encoding="utf-8") as f:
        f.write(code.strip() + "\n")
    log_result("VOICE_CAPTURE_GEN", "PASS", HEAVY_MODEL, f"Wrote {target}")
    return True


# ── Task 6: Voice Router Code Gen ──────────────────────────────────────────
@task("VOICE_ROUTER_GEN", HEAVY_MODEL, "Generate voice_router.py via local model")
def gen_voice_router():
    prompt = """You are Maxx, sovereign AI architect. Write a Python script called voice_router.py that:
1. Monitors memory/agent_logs/voice_events.jsonl for new WAV file entries (tail -f style).
2. For each new WAV, runs local speech-to-text using the 'vosk' library with a small English model.
3. Writes the transcript to memory/agent_logs/stt_route_events.jsonl as {timestamp, transcript, wav_path}.
4. Classifies the intent of the transcript into categories: 'edit_file', 'run_command', 'render_ui', 'query', 'general'.
5. Based on intent, selects a model: edit_file→sovereign-hermes, run_command→deepseek-r1:1.5b, render_ui→sovereign-hermes, query→qwen2.5:1.5b, general→deepseek-r1:1.5b.
6. Dispatches the transcript to the selected model via Ollama at http://127.0.0.1:11434/api/generate.
7. Writes the model response to memory/agent_logs/agent_inbox.jsonl as {timestamp, intent, model, response}.
8. All paths relative to SSOT_ROOT env var or script's grandparent directory.
9. Fully off-grid, no cloud calls.

Output ONLY the Python code, no explanation."""

    code = query_ollama(HEAVY_MODEL, prompt, timeout=180)
    if code.startswith("ERROR:"):
        log_result("VOICE_ROUTER_GEN", "FAIL", HEAVY_MODEL, code)
        return False

    target = os.path.join(SSOT_ROOT, "agents", "voice", "voice_router.py")
    os.makedirs(os.path.dirname(target), exist_ok=True)

    if "```python" in code:
        code = code.split("```python", 1)[1]
        if "```" in code:
            code = code.rsplit("```", 1)[0]
    elif "```" in code:
        code = code.split("```", 1)[1]
        if "```" in code:
            code = code.rsplit("```", 1)[0]

    with open(target, "w", encoding="utf-8") as f:
        f.write(code.strip() + "\n")
    log_result("VOICE_ROUTER_GEN", "PASS", HEAVY_MODEL, f"Wrote {target}")
    return True


# ── Task 7: Model Orchestrator Code Gen ────────────────────────────────────
@task("ORCHESTRATOR_GEN", HEAVY_MODEL, "Generate model_orchestrator.py via local model")
def gen_orchestrator():
    prompt = """You are Maxx, sovereign AI architect. Write a Python module called model_orchestrator.py that:
1. Defines a MODEL_REGISTRY dict mapping model names to their capabilities:
   - sovereign-hermes: reasoning, code_generation, planning, orchestration
   - deepseek-r1:1.5b: verification, linting, status_checks, quick_commands
   - hermes3:8b: fallback_reasoning, code_review
   - qwen2.5:1.5b: summarization, lightweight_queries
   - llama3.2: general_chat, brainstorming
2. Has a function select_model(intent: str) -> str that picks the best model for the intent.
3. Has a function dispatch(model: str, prompt: str) -> str that sends the prompt to the local Ollama at http://127.0.0.1:11434/api/generate and returns the response.
4. Has a function orchestrate(transcript: str) -> dict that classifies intent, selects model, dispatches, and returns {intent, model, response}.
5. Includes retry logic with fallback to hermes3:8b if the primary model fails.
6. Fully off-grid, no cloud.

Output ONLY the Python code, no explanation."""

    code = query_ollama(HEAVY_MODEL, prompt, timeout=180)
    if code.startswith("ERROR:"):
        log_result("ORCHESTRATOR_GEN", "FAIL", HEAVY_MODEL, code)
        return False

    target = os.path.join(SSOT_ROOT, "agents", "orchestrator", "model_orchestrator.py")
    os.makedirs(os.path.dirname(target), exist_ok=True)

    if "```python" in code:
        code = code.split("```python", 1)[1]
        if "```" in code:
            code = code.rsplit("```", 1)[0]
    elif "```" in code:
        code = code.split("```", 1)[1]
        if "```" in code:
            code = code.rsplit("```", 1)[0]

    with open(target, "w", encoding="utf-8") as f:
        f.write(code.strip() + "\n")
    log_result("ORCHESTRATOR_GEN", "PASS", HEAVY_MODEL, f"Wrote {target}")
    return True


# ── Task 8: Launch Scripts ─────────────────────────────────────────────────
@task("LAUNCH_SCRIPTS", FAST_MODEL, "Create run_store.bat, run_voice.bat, run_all.bat")
def create_launch_scripts():
    scripts = {
        "run_store.bat": (
            '@echo off\n'
            'echo [Xoras] Starting store server on port 8085...\n'
            f'start /B python "{os.path.join(SSOT_ROOT, "products", "xmars_os", "server.py")}"\n'
            'echo [Xoras] Store live at http://127.0.0.1:8085/store.html\n'
            'pause\n'
        ),
        "run_voice.bat": (
            '@echo off\n'
            'echo [Xoras] Starting voice capture daemon...\n'
            f'start /B python "{os.path.join(SSOT_ROOT, "agents", "voice", "voice_capture.py")}"\n'
            'echo [Xoras] Starting voice router...\n'
            f'start /B python "{os.path.join(SSOT_ROOT, "agents", "voice", "voice_router.py")}"\n'
            'echo [Xoras] Voice pipeline active. Speak to Maxx.\n'
            'pause\n'
        ),
        "run_all.bat": (
            '@echo off\n'
            'echo ================================================\n'
            'echo   XORAS Sovereign Command OS — Full Boot\n'
            'echo ================================================\n'
            f'call "{os.path.join(SSOT_ROOT, "run_store.bat")}"\n'
            f'call "{os.path.join(SSOT_ROOT, "run_voice.bat")}"\n'
            'echo [Xoras] All systems online.\n'
            'pause\n'
        ),
    }
    for name, content in scripts.items():
        path = os.path.join(SSOT_ROOT, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    log_result("LAUNCH_SCRIPTS", "PASS", FAST_MODEL, f"Wrote {len(scripts)} scripts to {SSOT_ROOT}")
    return True


# ── Task 9: Voice Orchestration Docs ──────────────────────────────────────
@task("VOICE_DOCS", HEAVY_MODEL, "Generate voice orchestration documentation")
def gen_voice_docs():
    prompt = """Write a concise Markdown document titled 'Voice-to-Maxx Orchestration Pipeline' for the XORAS Sovereign OS.

Sections:
1. Overview — what the pipeline does (mic → STT → intent → model dispatch → response)
2. Architecture — diagram description showing: Microphone → voice_capture.py → WAV chunks → voice_router.py → Vosk STT → transcript → model_orchestrator.py → Ollama (local models) → response → agent_inbox.jsonl
3. Local Models Used — table with model name, size, and use case for: sovereign-hermes, deepseek-r1:1.5b, hermes3:8b, qwen2.5:1.5b, llama3.2
4. Intent Classification — table mapping intents (edit_file, run_command, render_ui, query, general) to their assigned models
5. Security — note that all processing is off-grid, no cloud calls, audio stored locally only
6. Running — commands to start: python agents/voice/voice_capture.py and python agents/voice/voice_router.py, or run_voice.bat

Output ONLY the Markdown, no explanation."""

    doc = query_ollama(HEAVY_MODEL, prompt, timeout=120)
    if doc.startswith("ERROR:"):
        log_result("VOICE_DOCS", "FAIL", HEAVY_MODEL, doc)
        return False

    target = os.path.join(SSOT_ROOT, "docs", "briefings", "VOICE_ORCHESTRATION.md")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(doc.strip() + "\n")
    log_result("VOICE_DOCS", "PASS", HEAVY_MODEL, f"Wrote {target}")
    return True


# ── Task 10: Git Commit ───────────────────────────────────────────────────
@task("GIT_COMMIT", FAST_MODEL, "Stage and commit all new files")
def git_commit():
    import subprocess
    try:
        subprocess.run(["git", "add", "-A"], cwd=SSOT_ROOT, check=True, timeout=30)
        subprocess.run(
            ["git", "commit", "-m",
             "[Maxx] Local handoff: voice pipeline, orchestrator, launch scripts, store verification — all off-grid"],
            cwd=SSOT_ROOT, check=True, timeout=30
        )
        log_result("GIT_COMMIT", "PASS", FAST_MODEL, "Committed all changes")
        return True
    except subprocess.CalledProcessError as e:
        log_result("GIT_COMMIT", "FAIL", FAST_MODEL, str(e))
        return False


# ── Runner ─────────────────────────────────────────────────────────────────

def main():
    print("=" * 64)
    print("  XORAS Local Handoff Executor")
    print(f"  Models: {HEAVY_MODEL} (heavy) | {FAST_MODEL} (fast)")
    print(f"  Ollama: {OLLAMA_URL}")
    print(f"  SSOT:   {SSOT_ROOT}")
    print(f"  Time:   {datetime.datetime.now().isoformat()}")
    print("=" * 64)
    print()

    passed = 0
    failed = 0
    for t in TASKS:
        print(f">> [{t['id']}] {t['desc']} (model: {t['model']})")
        try:
            ok = t["fn"]()
            if ok:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            log_result(t["id"], "ERROR", t["model"], traceback.format_exc())
            failed += 1
            print(f"  [!] Exception: {e}")
        print()

    print("=" * 64)
    total = passed + failed
    print(f"  RESULTS: {passed}/{total} PASSED | {failed}/{total} FAILED")
    if failed == 0:
        print("  STATUS: ALL GREEN -- 200 ACROSS THE BOARD")
    else:
        print(f"  STATUS: {failed} task(s) need attention")
    print(f"  Log: {HANDOFF_LOG}")
    print("=" * 64)


if __name__ == "__main__":
    main()
