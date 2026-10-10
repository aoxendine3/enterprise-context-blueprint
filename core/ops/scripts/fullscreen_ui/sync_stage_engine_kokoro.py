import os, sys, json, time, threading, urllib.request, subprocess
import soundfile as sf

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STAGE_DIR = SCRIPT_DIR
SSOT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..'))
MODELS_DIR = os.path.join(SSOT_ROOT, 'capabilities', 'neural_models')
MANIFEST_PATH = os.path.join(SSOT_ROOT, 'identity', 'sovereign_citizens_manifest.json')

TIMING_JSON = os.path.join(STAGE_DIR, 'current_timing.json')
STATE_FILE = os.path.join(STAGE_DIR, 'current_image.txt')
TRANSCRIPT_FILE = os.path.join(STAGE_DIR, 'current_transcript.txt')
WAV_FILE = os.path.join(STAGE_DIR, 'live_speech.wav')
MP3_FILE = os.path.join(STAGE_DIR, 'live_elevenlabs.mp3')

# Key Rotation Array for ElevenLabs
KEYS_TO_TRY = []
if os.environ.get("ELEVENLABS_API_KEY"):
    KEYS_TO_TRY.append(os.environ.get("ELEVENLABS_API_KEY"))

env_file = os.path.expanduser("~/.env")
if os.path.exists(env_file):
    try:
        with open(env_file, 'r') as f:
            for line in f:
                if "ELEVENLABS_API_KEY" in line:
                    key_val = line.split("=")[-1].strip().strip('"').strip("'")
                    if key_val and key_val not in KEYS_TO_TRY:
                        KEYS_TO_TRY.append(key_val)
    except Exception:
        pass

DEFAULT_KEYS = [
    "sk_d55face808a29a43e637767eb1a6ab62a490d58ca4a5925b"
]
for k in DEFAULT_KEYS:
    if k not in KEYS_TO_TRY:
        KEYS_TO_TRY.append(k)

ELEVENLABS_VOICES = {
    "maxx": "JBFqnCBsd6RMkjVDRZzb",      # George
    "clara": "21m00Tcm4TlvDq8ikWAM",     # Rachel
    "vance": "IKne3meq5aSn9XLyUdCD",     # Charlie
    "jarvis": "pNInz6obpgDQGcFmaJgB",    # Adam
    "daxx": "ErXwobaYiN019PkySvjV",      # Antoni
    "john": "VR6AewLTigWG4xSOukaG",      # Arnold
    "selene": "EXAVITQu4vr4xnSDxMaL",    # Bella
    "eden": "cgSgspJ2msm6clMCkdW9",      # Jessica
    "sophia": "XrExE9yKIg1WjnnlVkGX",    # Matilda
    "aurelius": "N2lrfwcwuACfkwE3moXM",  # Callum
    "xoras": "onwK4e9ZLuTAKqWW03F9"      # Daniel
}

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

def speak_via_elevenlabs(agent_name, text):
    agent_key = agent_name.lower().replace(" ", "_").replace("dr._", "").replace("dr_", "")
    voice_id = ELEVENLABS_VOICES.get(agent_key, "JBFqnCBsd6RMkjVDRZzb")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    payload = {
        "text": text,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {
            "stability": 0.48,
            "similarity_boost": 0.85,
            "style": 0.12,
            "use_speaker_boost": True
        }
    }
    data_bytes = json.dumps(payload).encode('utf-8')
    
    for api_key in KEYS_TO_TRY:
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        req = urllib.request.Request(url, data=data_bytes, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                audio_data = resp.read()
                if len(audio_data) > 100:
                    with open(MP3_FILE, "wb") as f:
                        f.write(audio_data)
                    os.system(f"afplay '{MP3_FILE}'")
                    return True
        except Exception:
            continue
    return False

def speak_agent(agent_name, text):
    # 1. Primary: Try ElevenLabs with Key Rotation
    if speak_via_elevenlabs(agent_name, text):
        return

    # 2. Fallback: Local Kokoro ONNX Engine
    global VOICE_MAP
    VOICE_MAP = load_voice_map_from_manifest()
    
    agent_key = agent_name.lower().replace(" ", "_").replace("dr._", "").replace("dr_", "")
    voice_id = VOICE_MAP.get(agent_key, "am_adam")
    
    engine = get_kokoro_engine()
    samples, sample_rate = engine.create(text, voice=voice_id, speed=1.0, lang="en-us")
    
    sf.write(WAV_FILE, samples, sample_rate)
    os.system(f"afplay '{WAV_FILE}'")

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        speak_agent(sys.argv[1], sys.argv[2])
