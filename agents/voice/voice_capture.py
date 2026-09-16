"""
Voice Capture Daemon — XORAS Sovereign OS
Continuous 16kHz 16-bit mono audio recording from microphone.
Writes 5-second chunks locally and logs events to voice_events.jsonl.
Zero cloud token burn. Completely off-grid.
"""

import os
import sys
import json
import time
import wave
import logging
import threading
from datetime import datetime

# Determine SSOT root
SSOT_ROOT = os.environ.get(
    "SSOT_ROOT",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
)
LOG_DIR = os.path.join(SSOT_ROOT, "memory", "agent_logs")
CHUNKS_DIR = os.path.join(LOG_DIR, "voice_chunks")
VOICE_EVENTS = os.path.join(LOG_DIR, "voice_events.jsonl")

os.makedirs(CHUNKS_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [VoiceCapture] %(message)s"
)
log = logging.getLogger("voice_capture")

_stop_event = threading.Event()

def save_wav(filename: str, audio_data: bytes, sample_rate: int = 16000):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data)

def record_loop():
    try:
        import sounddevice as sd
    except ImportError:
        log.error("sounddevice package not found. Please install via: pip install sounddevice numpy")
        return

    sample_rate = 16000
    duration = 5  # seconds
    frames_per_chunk = int(duration * sample_rate)

    log.info("Starting audio recording loop (16kHz 16-bit mono, 5s chunks)...")

    while not _stop_event.is_set():
        try:
            recording = sd.rec(frames_per_chunk, samplerate=sample_rate, channels=1, dtype='int16')
            sd.wait()

            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            wav_filename = f"voice_{timestamp_str}.wav"
            wav_path = os.path.join(CHUNKS_DIR, wav_filename)

            save_wav(wav_path, recording.tobytes(), sample_rate=sample_rate)

            event_data = {
                "timestamp": datetime.now().isoformat(),
                "wav_path": os.path.abspath(wav_path)
            }
            with open(VOICE_EVENTS, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_data) + "\n")

            log.info("Recorded: %s", wav_filename)
        except Exception as e:
            log.error("Error during audio capture cycle: %s", e)
            time.sleep(1)

def main():
    t = threading.Thread(target=record_loop, daemon=True)
    t.start()
    try:
        while t.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        log.info("KeyboardInterrupt received. Stopping voice capture.")
        _stop_event.set()
        t.join(timeout=2.0)

if __name__ == "__main__":
    main()
