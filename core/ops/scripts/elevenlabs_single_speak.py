#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SSOT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
MANIFEST_PATH = os.path.join(SSOT_ROOT, 'identity', 'sovereign_citizens_manifest.json')

# Key Rotation Array: primary key from env / .env, backup keys
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

# Default embedded fallback keys
DEFAULT_KEYS = [
    "sk_d55face808a29a43e637767eb1a6ab62a490d58ca4a5925b"
]
for k in DEFAULT_KEYS:
    if k not in KEYS_TO_TRY:
        KEYS_TO_TRY.append(k)

# ElevenLabs voice mappings
VOICE_MAP = {
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

def speak_elevenlabs(agent_name, text):
    agent_key = agent_name.lower().replace(" ", "_")
    voice_id = VOICE_MAP.get(agent_key, "JBFqnCBsd6RMkjVDRZzb")
    
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
    
    audio_path = f"/tmp/elevenlabs_{agent_key}.mp3"
    
    for api_key in KEYS_TO_TRY:
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        req = urllib.request.Request(url, data=data_bytes, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                audio_data = resp.read()
                if len(audio_data) > 100:
                    with open(audio_path, "wb") as f:
                        f.write(audio_data)
                    # Play live on hardware speaker
                    subprocess.run(["afplay", audio_path], check=False)
                    return True
        except Exception as e:
            # Try next API key
            continue
            
    return False

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        success = speak_elevenlabs(sys.argv[1], sys.argv[2])
        if not success:
            sys.exit(1)
        sys.exit(0)
