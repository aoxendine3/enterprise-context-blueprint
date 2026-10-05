import os, sys, json, time, threading, soundfile as sf

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STAGE_DIR = SCRIPT_DIR
SSOT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..'))
MODELS_DIR = os.path.join(SSOT_ROOT, 'capabilities', 'neural_models')
MANIFEST_PATH = os.path.join(SSOT_ROOT, 'identity', 'sovereign_citizens_manifest.json')

TIMING_JSON = os.path.join(STAGE_DIR, 'current_timing.json')
STATE_FILE = os.path.join(STAGE_DIR, 'current_image.txt')
TRANSCRIPT_FILE = os.path.join(STAGE_DIR, 'current_transcript.txt')
WAV_FILE = os.path.join(STAGE_DIR, 'live_speech.wav')

def load_voice_map_from_manifest():
    voice_map = {}
    if os.path.exists(MANIFEST_PATH):
        try:
            with open(MANIFEST_PATH, 'r') as f:
                data = json.load(f)
            for c in data.get('citizens', []):
                aid = c.get('agent_id', '').lower()
                vid = c.get('kokoro_voice_id', 'am_adam')
                if aid:
                    voice_map[aid] = vid
                    voice_map[f"dr_{aid}"] = vid
        except Exception:
            pass
    return voice_map

VOICE_MAP = load_voice_map_from_manifest()

_KOKORO_ENGINE = None
_KOKORO_LOCK = threading.Lock()

def get_kokoro_engine():
    global _KOKORO_ENGINE
    if _KOKORO_ENGINE is None:
        with _KOKORO_LOCK:
            if _KOKORO_ENGINE is None:
                from kokoro_onnx import Kokoro
                model_path = os.path.join(MODELS_DIR, 'kokoro-v1.0.onnx')
                voices_path = os.path.join(MODELS_DIR, 'voices.bin')
                _KOKORO_ENGINE = Kokoro(model_path, voices_path)
    return _KOKORO_ENGINE

def normalize_text(text):
    return text.strip()

def speak_agent(agent_name, text):
    global VOICE_MAP
    VOICE_MAP = load_voice_map_from_manifest() # Dynamic refresh on every call
    
    agent_key = agent_name.lower().replace(" ", "_").replace("dr._", "").replace("dr_", "")
    voice_id = VOICE_MAP.get(agent_key, "am_adam")
    
    engine = get_kokoro_engine()
    samples, sample_rate = engine.create(text, voice=voice_id, speed=1.0, lang="en-us")
    
    sf.write(WAV_FILE, samples, sample_rate)
    
    # Play WAV file over hardware speakers
    os.system(f"afplay '{WAV_FILE}'")

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        speak_agent(sys.argv[1], sys.argv[2])
