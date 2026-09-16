import os
import json
import logging
import sounddevice as sd
import threading
from datetime import datetime
import numpy as np

# Set default SSOT_ROOT
SSOT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(filename=os.path.join(SSOT_ROOT, 'memory', 'agent_logs', 'voice_capture.log'), level=logging.INFO)

def save_audio(data, filename):
    try:
        sd.wavwrite(data, filename)
    except Exception as e:
        logging.error(f"Failed to save audio: {e}")

def save_event(event, wav_path):
    try:
        with open(os.path.join(SSOT_ROOT, 'memory', 'agent_logs', 'voice_events.jsonl'), 'a') as f:
            f.write(f"{event}\n")
    except Exception as e:
        logging.error(f"Failed to save event: {e}")

def record_audio():
    chunk_duration = 5
    fs = 16000
    duration = chunk_duration
    myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait(int(duration * fs))

    timestamp = datetime.now().isoformat()
    wav_path = os.path.join(SSOT_ROOT, 'memory', 'agent_logs', 'voice_chunks', f"{timestamp}.wav")
    save_audio(myrecording, wav_path)
    event = f"{timestamp}, {wav_path}"
    save_event(event, wav_path)

    return timestamp, wav_path

def main():
    while True:
        try:
            threading.Thread(target=record_audio).start()
        except KeyboardInterrupt:
            logging.info("Shutting down...")
            break
        except Exception as e:
            logging.error(f"Error in main loop: {e}")

if __name__ == "__main__":
    main()
``
