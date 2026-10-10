import os
import sys
import json
import urllib.request
import subprocess

API_KEY = os.environ.get("ELEVENLABS_API_KEY", "sk_d55face808a29a43e637767eb1a6ab62a490d58ca4a5925b")

# Verified active default ElevenLabs voices for each agent persona:
VOICE_MAP = {
    "JARVIS": "pNInz6obpgDQGcFmaJgB", # Adam (Deep, Command)
    "MAXX": "JBFqnCBsd6RMkjVDRZzb",   # George (Warm, Technical Mentorship)
    "CLARA": "21m00Tcm4TlvDq8ikWAM",  # Rachel (Calm, Clinical Precision)
    "VANCE": "IKne3meq5aSn9XLyUdCD"   # Charlie (Analytical, Falsification)
}

def synthesize_line(speaker, text, index, output_dir):
    voice_id = VOICE_MAP.get(speaker, "JBFqnCBsd6RMkjVDRZzb")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": API_KEY
    }
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
    
    file_path = os.path.join(output_dir, f"line_{index:02d}_{speaker}.mp3")
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            audio_data = resp.read()
            with open(file_path, "wb") as f:
                f.write(audio_data)
            print(f"[SYNTHESIZED] Line {index:02d} ({speaker} via {voice_id}): {file_path} ({len(audio_data)} bytes)")
            return file_path
    except Exception as e:
        print(f"[ERROR] Failed line {index:02d} ({speaker}): {e}", file=sys.stderr)
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 compile_collective_audio.py <script_json_path>")
        sys.exit(1)
        
    script_json_path = sys.argv[1]
    with open(script_json_path, "r") as f:
        lines = json.load(f)
        
    output_dir = "memory/agent_logs/collective_chunks"
    os.makedirs(output_dir, exist_ok=True)
    
    audio_files = []
    for idx, item in enumerate(lines, 1):
        speaker = item["speaker"]
        text = item["text"]
        fp = synthesize_line(speaker, text, idx, output_dir)
        if fp:
            audio_files.append(fp)
            
    if not audio_files:
        print("[ERROR] No audio files synthesized!", file=sys.stderr)
        sys.exit(1)
        
    # Write ffmpeg concat file
    concat_list_path = os.path.join(output_dir, "concat_list.txt")
    with open(concat_list_path, "w") as f:
        for fp in audio_files:
            f.write(f"file '{os.path.abspath(fp)}'\n")
            
    master_output = "memory/agent_logs/collective_master_narration_multiagent.mp3"
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list_path, "-c", "copy", master_output
    ]
    subprocess.run(ffmpeg_cmd, check=True)
    print(f"\n[SUCCESS] Master Collective Multi-Agent Audio compiled: {master_output}")

if __name__ == "__main__":
    main()
