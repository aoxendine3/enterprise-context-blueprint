"""
Voice Router — Monitors voice events, runs local STT via Vosk,
classifies intent, and dispatches to sovereign-hermes via Ollama.
Fully off-grid. No cloud dependencies.
"""

import os
import sys
import json
import time
import wave
import logging
import urllib.request
import datetime

# ── Paths ───────────────────────────────────────────────────────────────────
SSOT_ROOT = os.environ.get(
    "SSOT_ROOT",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
)
LOG_DIR = os.path.join(SSOT_ROOT, "memory", "agent_logs")
VOICE_EVENTS = os.path.join(LOG_DIR, "voice_events.jsonl")
STT_EVENTS = os.path.join(LOG_DIR, "stt_route_events.jsonl")
AGENT_INBOX = os.path.join(LOG_DIR, "agent_inbox.jsonl")
VOSK_MODEL_PATH = os.path.join(SSOT_ROOT, "agents", "models", "vosk-model-small-en-us")

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
PRIMARY_MODEL = "sovereign-hermes"
FALLBACK_MODEL = "hermes3:8b"

os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [VoiceRouter] %(message)s"
)
log = logging.getLogger("voice_router")

# ── Intent Classification ───────────────────────────────────────────────────
INTENT_KEYWORDS = {
    "edit_file": ["edit", "modify", "change", "update", "fix", "refactor", "add to", "write to"],
    "run_command": ["run", "execute", "start", "launch", "build", "compile", "test", "deploy"],
    "render_ui": ["render", "show", "display", "preview", "design", "draw", "visualize", "ui"],
    "query": ["what", "why", "how", "explain", "describe", "tell me", "status", "check"],
    "general": []
}


def classify_intent(transcript: str) -> str:
    """Classify transcript into an intent category using keyword matching."""
    lower = transcript.lower().strip()
    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                return intent
    return "general"


# ── Ollama Dispatch ─────────────────────────────────────────────────────────
def dispatch_to_ollama(model: str, prompt: str, timeout: int = 120) -> str:
    """Send a prompt to a local Ollama model and return the response."""
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
        log.error("Model %s failed: %s", model, e)
        if model != FALLBACK_MODEL:
            log.info("Falling back to %s", FALLBACK_MODEL)
            return dispatch_to_ollama(FALLBACK_MODEL, prompt, timeout)
        return f"ERROR: {e}"


# ── STT via Vosk ────────────────────────────────────────────────────────────
def transcribe_wav(wav_path: str) -> str:
    """Transcribe a WAV file using Vosk offline speech recognition."""
    try:
        from vosk import Model, KaldiRecognizer
    except ImportError:
        log.warning("Vosk not installed. Install with: pip install vosk")
        log.warning("Returning empty transcript.")
        return ""

    if not os.path.isdir(VOSK_MODEL_PATH):
        log.warning("Vosk model not found at %s", VOSK_MODEL_PATH)
        log.warning("Download a model from https://alphacephei.com/vosk/models")
        return ""

    model = Model(VOSK_MODEL_PATH)

    with wave.open(wav_path, "rb") as wf:
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
            log.error("WAV must be mono 16-bit PCM: %s", wav_path)
            return ""

        recognizer = KaldiRecognizer(model, wf.getframerate())
        recognizer.SetWords(True)

        transcript_parts = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "")
                if text:
                    transcript_parts.append(text)

        final = json.loads(recognizer.FinalResult())
        final_text = final.get("text", "")
        if final_text:
            transcript_parts.append(final_text)

    return " ".join(transcript_parts)


# ── Event Journal Writers ───────────────────────────────────────────────────
def write_stt_event(transcript: str, wav_path: str):
    """Log the STT result to stt_route_events.jsonl."""
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "transcript": transcript,
        "wav_path": wav_path
    }
    with open(STT_EVENTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def write_inbox_event(intent: str, model: str, response: str, transcript: str):
    """Log the model response to agent_inbox.jsonl."""
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "intent": intent,
        "model": model,
        "transcript": transcript,
        "response": response[:4000]
    }
    with open(AGENT_INBOX, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# ── Main Loop (Tail voice_events.jsonl) ─────────────────────────────────────
def tail_events():
    """
    Continuously monitor voice_events.jsonl for new entries.
    For each new WAV, run STT, classify intent, dispatch to sovereign-hermes,
    and log the result.
    """
    log.info("Voice Router started.")
    log.info("Monitoring: %s", VOICE_EVENTS)
    log.info("Primary model: %s", PRIMARY_MODEL)
    log.info("SSOT root: %s", SSOT_ROOT)

    # Track how many lines we've already processed
    processed_lines = 0

    # If the events file doesn't exist yet, wait for it
    while not os.path.exists(VOICE_EVENTS):
        log.info("Waiting for voice_events.jsonl to appear...")
        time.sleep(2)

    while True:
        try:
            with open(VOICE_EVENTS, "r", encoding="utf-8") as f:
                lines = f.readlines()

            new_lines = lines[processed_lines:]
            if not new_lines:
                time.sleep(1)
                continue

            for line in new_lines:
                line = line.strip()
                if not line:
                    processed_lines += 1
                    continue

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    log.warning("Skipping malformed line: %s", line[:100])
                    processed_lines += 1
                    continue

                wav_path = event.get("wav_path", "")
                if not wav_path or not os.path.exists(wav_path):
                    log.warning("WAV not found: %s", wav_path)
                    processed_lines += 1
                    continue

                # 1. Transcribe
                log.info("Transcribing: %s", os.path.basename(wav_path))
                transcript = transcribe_wav(wav_path)

                if not transcript:
                    log.info("Empty transcript, skipping.")
                    processed_lines += 1
                    continue

                log.info("Transcript: %s", transcript[:120])
                write_stt_event(transcript, wav_path)

                # 2. Classify intent
                intent = classify_intent(transcript)
                log.info("Intent: %s", intent)

                # 3. Dispatch to sovereign-hermes
                prompt = f"[Intent: {intent}] User said: {transcript}"
                log.info("Dispatching to %s...", PRIMARY_MODEL)
                response = dispatch_to_ollama(PRIMARY_MODEL, prompt)
                log.info("Response received (%d chars)", len(response))

                # 4. Log result
                write_inbox_event(intent, PRIMARY_MODEL, response, transcript)

                processed_lines += 1

        except KeyboardInterrupt:
            log.info("Voice Router shutting down.")
            break
        except Exception as e:
            log.error("Error in main loop: %s", e)
            time.sleep(2)


if __name__ == "__main__":
    tail_events()
