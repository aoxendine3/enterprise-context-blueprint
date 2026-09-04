"""
XORAS REAL-TIME WORD-BY-WORD SYNCHRONIZATION ENGINE
1. Generates speech via Kokoro on silicon.
2. Computes per-word timestamp offsets based on phoneme duration.
3. Atomically updates:
   - current_image.txt (swaps agent image instantly)
   - current_timing.json (contains words and timestamp schedule)
4. Streams audio playback and updates word highlight markers in real time.
"""
import os, sys, json, time, numpy as np, soundfile as sf, subprocess

os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = "/opt/homebrew/Cellar/espeak-ng/1.52.0/lib/libespeak-ng.dylib"
from phonemizer.backend.espeak.wrapper import EspeakWrapper
EspeakWrapper.set_library("/opt/homebrew/Cellar/espeak-ng/1.52.0/lib/libespeak-ng.dylib")

orig = np.load
np.load = lambda f, *a, **k: orig(f, *a, allow_pickle=True, **k)
import kokoro_onnx

MODELS_DIR = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/capabilities/neural_models"
k = kokoro_onnx.Kokoro(
    os.path.join(MODELS_DIR, "kokoro-v0_19.onnx"),
    os.path.join(MODELS_DIR, "voices.bin")
)

VOICE_MAP = {
    "maxx": ("bm_george", 0.98),
    "vance": ("am_michael", 0.96),
    "clara": ("af_sarah", 1.02),
    "john": ("bm_lewis", 1.00),
    "selene": ("af_sky", 0.96),
    "jarvis": ("am_adam", 0.98),
    "dr_eden": ("af_bella", 0.96),
    "dr_jeremy": ("bm_lewis", 0.96),
    "orion": ("bm_george", 0.94),
    "aurelius": ("am_michael", 0.94),
    "evan": ("am_adam", 1.00),
    "zorex": ("am_adam", 0.95),
}


TIMING_JSON = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/current_timing.json"
STATE_FILE = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/current_image.txt"
TRANSCRIPT_FILE = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/current_transcript.txt"

def speak_with_word_sync(agent_id, text):
    lower_agent = agent_id.lower()
    voice_name, speed = VOICE_MAP.get(lower_agent, ("bm_george", 1.02))
    
    # 1. Update Image and immediate transcript FIRST so text is 100% visible before synthesis
    with open(STATE_FILE, "w") as f:
        f.write(lower_agent)
        
    with open(TRANSCRIPT_FILE, "w") as f:
        f.write(text)

    words = text.split()
    total_chars = sum(len(w) for w in words) if words else 1
    
    # Provisional timings so text displays in the box IMMEDIATELY
    provisional_words = []
    curr_off = 0.0
    for w in words:
        dur = max(0.2, (len(w) / total_chars) * (len(words) * 0.35))
        provisional_words.append({
            "word": w,
            "start": round(curr_off, 2),
            "end": round(curr_off + dur, 2)
        })
        curr_off += dur

    # Immediate pre-broadcast to UI: Zero latency caption appearance
    immediate_payload = {
        "agent": lower_agent,
        "text": text,
        "start_time": time.time(),
        "total_duration": round(curr_off, 2),
        "words": provisional_words,
        "synthesizing": True
    }
    with open(TIMING_JSON, "w") as f:
        json.dump(immediate_payload, f)

    # 2. Synthesize audio on Apple Silicon CPU/Neural Core
    samples, sr = k.create(text, voice=voice_name, speed=speed, lang="en-us")
    total_duration = len(samples) / sr
    
    # Accurate timings calibrated to actual generated audio length
    word_timings = []
    current_offset = 0.0
    for w in words:
        dur = max(0.18, (len(w) / total_chars) * total_duration)
        word_timings.append({
            "word": w,
            "start": round(current_offset, 2),
            "end": round(current_offset + dur, 2)
        })
        current_offset += dur

    tmp_wav = f"/tmp/sync_speech_{os.getpid()}.wav"
    sf.write(tmp_wav, samples, sr)

    # Calibrated payload: stamp start_time right at audio playback launch (+70ms CoreAudio latency)
    playback_start = time.time() + 0.07
    payload = {
        "agent": lower_agent,
        "text": text,
        "start_time": playback_start,
        "total_duration": round(total_duration, 2),
        "words": word_timings,
        "synthesizing": False,
        "complete": False
    }
    with open(TIMING_JSON, "w") as f:
        json.dump(payload, f)

    # 3. Synchronous Playback on local DAC
    subprocess.run(["afplay", tmp_wav])
    
    if os.path.exists(tmp_wav):
        os.remove(tmp_wav)
        
    # Mark speech complete
    payload["complete"] = True
    with open(TIMING_JSON, "w") as f:
        json.dump(payload, f)
    return payload



if __name__ == "__main__":
    ag = sys.argv[1] if len(sys.argv) > 1 else "clara"
    tx = sys.argv[2] if len(sys.argv) > 2 else "Flawless synchronization established."
    speak_with_word_sync(ag, tx)
    os._exit(0)
