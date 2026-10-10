import os
import sys
import json
import urllib.request

API_KEY = os.environ.get("ELEVENLABS_API_KEY", "sk_d55face808a29a43e637767eb1a6ab62a490d58ca4a5925b")
# George / Narrative Voice ID: JBFqnCBsd6RMkjVDRZzb or Eric: DdNHQEC7ANncWzt6Iivg
VOICE_ID = sys.argv[1] if len(sys.argv) > 1 else "JBFqnCBsd6RMkjVDRZzb" # George
OUTPUT_PATH = sys.argv[2] if len(sys.argv) > 2 else "memory/agent_logs/industry_bottleneck_narration.mp3"
TEXT = sys.argv[3] if len(sys.argv) > 3 else "The fundamental bottleneck in modern AI isn't raw compute or context window size. It's context collapse. As autonomous agents execute complex, long-horizon workflows past fifty tool calls, standard attention mechanisms suffer from linear state degradation. Memory bleeds, past execution context becomes noise, and agents enter destructive hallucination loops."

url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
headers = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json",
    "xi-api-key": API_KEY
}

payload = {
    "text": TEXT,
    "model_id": "eleven_turbo_v2_5",
    "voice_settings": {
        "stability": 0.45,
        "similarity_boost": 0.85,
        "style": 0.15,
        "use_speaker_boost": True
    }
}

req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        audio_data = response.read()
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        with open(OUTPUT_PATH, "wb") as f:
            f.write(audio_data)
        print(f"[SUCCESS] ElevenLabs audio saved to: {OUTPUT_PATH} ({len(audio_data)} bytes)")
except Exception as e:
    print(f"[ERROR] Failed to synthesize via ElevenLabs: {e}", file=sys.stderr)
    sys.exit(1)
