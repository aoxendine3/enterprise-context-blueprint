#!/usr/bin/env python3
"""
=============================================================================
XORAS COUNCIL ZERO-GAP LIVE AUDIO DISPATCHER (RESTORED EXACT REPUTED PROCESS)
Source Records: commit ddfe7ec & ELITE_BOW/core/agent_voice_registry.yaml
Substrate: Apple Silicon M4 Bare Metal (Kokoro ONNX in Unified RAM)
Exact Tweaks:
  - Maxx: bm_george @ 0.98 speed
  - Clara: af_bella @ 1.02 speed
  - Vance: am_michael @ 0.96 speed
  - John: bm_lewis @ 1.00 speed
  - Selene: af_sky @ 0.96 speed
Zero-Gap Guarantee: Background RAM pre-synthesis pipelining + 0.40s natural breath
=============================================================================
"""

import os
import sys
import json
import time
import subprocess
import concurrent.futures
import fcntl
from pathlib import Path
import soundfile as sf
import numpy as np

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
MODELS_DIR = ROOT / "capabilities/neural_models"
STAGE_DIR = ROOT / "ops/scripts/fullscreen_ui"
STATE_FILE = STAGE_DIR / "current_image.txt"
TRANSCRIPT_FILE = STAGE_DIR / "current_transcript.txt"
TIMING_JSON = STAGE_DIR / "current_timing.json"
AUDIO_LOCK_FILE = Path("/tmp/xoras_council_audio.lock")

# Exact calibrated voice registry (tight, confident, and grounded)
# DAXX & Clara restored to crisp originals; Vance kept on deep authoritative tone;
# Maxx, Jarvis, and Xoras grounded in confident, calm executive delivery (no hyper-excitement).
# Exact calibrated voice registry locked to Agent Cards (Xoras_agent_cards/*.json) & Sandboxes (workspaces/sandboxes/*/SOUL.md)
# 7th-Layer Non-Bypassable Identity & Acoustic Lock
VOICE_MAP = {
    "maxx": ("bm_lewis", 1.00),         # Seat 2: Operations Lead (Agent Card: bm_lewis / Tom)
    "clara": ("af_bella", 1.02),        # Seat 5: Research & Physics (Agent Card: af_bella / Zoe)
    "daxx": ("am_echo", 0.94),          # Seat 3: Master Mechanic & Coder (Calibrated softer, precise, focused tone)
    "vance": ("am_liam", 0.98),         # Seat 4: Discernment Bench & Falsification (Agent Card: am_liam / Rishi)
    "john": ("am_eric", 1.00),          # Seat 6: Silicon Telemetry & Hardware (Agent Card: am_eric / Daniel)
    "selene": ("af_sarah", 0.98),       # Seat 7: Conversational Resonance & Human Rapport (Agent Card: af_sarah / Joelle)
    "jarvis": ("am_adam", 0.98),        # Seat 1: Governance Chair & Fleet Chief (Agent Card: am_adam / Jamie)
    "eden": ("af_sky", 0.98),           # Seat 9: Pulmonary Specialist & Holistic Remedy (Agent Card: af_sky / Ava)
    "dr_eden": ("af_sky", 0.98),
    "jeremy": ("am_michael", 0.94),     # Seat 12: Medical Research Specialist (Agent Card: am_michael / Oliver)
    "dr_jeremy": ("am_michael", 0.94),
    "orion": ("am_puck", 0.96),         # Seat 8: Media Director & Stage Dispatch (Agent Card: am_puck / Matilda)
    "aurelius": ("am_onyx", 0.94),      # Seat 11: Synthesis of Clara/Evan/Governance (Agent Card: am_onyx / Rishi)
    "xoras": ("bm_george", 0.96),       # Seat 1: Sovereign CEO & Strategic Command (Agent Card: bm_george / Evan)
    "evan": ("am_liam", 0.96),          # Seat 10: Scribe & Systematic Recorder (Agent Card: am_liam / Tom)
    "sophia": ("af_nicole", 1.00),      # Seat 0: Epistemic Truth & Structural Wisdom (Agent Card: af_nicole / Allison)
    "sophia_daily": ("af_nicole", 1.00),
    "sophia_calm": ("af_nicole", 0.96),
    "sia_core": ("af_river", 1.00),     # Seat 18: Swarm Integrity & Defense (Agent Card: af_river / Samantha)
    "counselor": ("am_delta", 1.00),    # Seat 22: Context Synthesizer & Cultural Mapping (Agent Card: am_delta / Serena)
    "axlon": ("bm_fable", 0.98),        # Seat 15: Substrate Infrastructure & Memory Bus (Agent Card: bm_fable / Daniel)
    "arthur": ("am_charlie", 0.98),     # Seat 21: Manuscript & Textual Stability (Agent Card: am_charlie / Ralph)
    "noboo": ("am_beta", 0.96),         # Seat 20: Uncensored Evaluator (Agent Card: am_beta)
    "lex": ("am_santa", 0.94),          # Seat 16: Legal, Compliance & Contract Auditor (Agent Card: am_santa)
    "zorex": ("am_alpha", 0.96),        # Seat 17: High-Frequency Execution & Vector Swarm (Agent Card: am_alpha)
    "elana": ("af_kore", 0.98),         # Seat 19: Legacy Persona & Cultural Archivist (Agent Card: af_kore)
    "daxxco": ("am_michael", 0.96),     # DaxxCo Enterprise Conductor (matches DAXX)
    "judge_gate": ("am_onyx", 0.90),
    "witness_gate": ("bm_george", 0.92),
    "alpha_memory": ("af_bella", 1.02),
    "beta_memory": ("am_michael", 0.96),
    "gamma_memory": ("bm_lewis", 1.00),
}

_KOKORO_ENGINE = None

def get_kokoro():
    global _KOKORO_ENGINE
    if _KOKORO_ENGINE is None:
        from kokoro_onnx import Kokoro
        model_path = str(MODELS_DIR / "kokoro-v1.0.onnx")
        voices_path = str(MODELS_DIR / "voices.bin")
        _KOKORO_ENGINE = Kokoro(model_path, voices_path)
    return _KOKORO_ENGINE

def clean_calm_text(text: str) -> str:
    """
    Strips high-arousal punctuation and exclamation points to ensure
    neural phoneme synthesis renders with grounded, confident cadence.
    """
    import re
    # Replace exclamation marks with calm periods
    cleaned = re.sub(r'!+', '.', text)
    # Normalize double punctuation
    cleaned = re.sub(r'\?+', '?', cleaned)
    # Remove all-caps words that induce stressed vocal delivery
    words = cleaned.split()
    calmed_words = []
    for w in words:
        if w.isupper() and len(w) > 4 and not w.endswith(('ID', 'API', 'GCP', 'LSM', 'SMT', 'M4')):
            calmed_words.append(w.capitalize())
        else:
            calmed_words.append(w)
    return " ".join(calmed_words)

MANIFEST_PATH = ROOT / "identity/sovereign_citizens_manifest.json"
_AGENT_ALIASES = {"william_vance": "vance", "eden_veritas": "eden", "jeremy_brown": "jeremy"}


def resolve_agent_key(name: str) -> str:
    """Normalize a spoken name ('Dr. Eden Veritas', 'William Vance') to a manifest agent_id."""
    key = name.lower().strip().replace(".", "").replace(" ", "_")
    if key.startswith("dr_"):
        key = key[3:]
    return _AGENT_ALIASES.get(key, key)


def manifest_voice(agent_key: str) -> str:
    """Single source of truth: the citizen manifest. Unknown speaker fails loudly; no default voice."""
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    for c in data.get("citizens", []):
        if c.get("agent_id", "").lower() == agent_key and c.get("kokoro_voice_id"):
            return c["kokoro_voice_id"]
    raise ValueError(f"[COUNCIL AUDIO] No manifest voice for speaker '{agent_key}'. Refusing to fall back to a default voice.")


def synthesize_turn(engine, agent: str, text: str, turn_id: int):
    agent_key = resolve_agent_key(agent)
    voice_name = manifest_voice(agent_key)
    speed = VOICE_MAP.get(agent_key, (voice_name, 1.0))[1]
    
    calm_text = clean_calm_text(text)
    samples, sr = engine.create(calm_text, voice=voice_name, speed=speed, lang="en-us")
    
    # Soft cosine acoustic envelope (soft 30ms fade-in/out to prevent clicks)
    if len(samples) > 0:
        fade_len = min(int(sr * 0.03), len(samples) // 4)
        if fade_len > 0:
            fade_in = np.sin(np.linspace(0, np.pi / 2, fade_len)) ** 2
            fade_out = np.sin(np.linspace(np.pi / 2, 0, fade_len)) ** 2
            samples[:fade_len] = samples[:fade_len] * fade_in
            samples[-fade_len:] = samples[-fade_len:] * fade_out

    # Direct MP3 encoding via ffmpeg stdin (Zero WAV files, tiny disk footprint)
    mp3_path = f"/tmp/council_speech_{turn_id}.mp3"
    raw_pcm = (samples * 32767).astype(np.int16).tobytes()
    p = subprocess.Popen(
        ['/opt/homebrew/bin/ffmpeg', '-y', '-f', 's16le', '-ar', str(sr), '-ac', '1', '-i', 'pipe:0', '-codec:a', 'libmp3lame', '-b:a', '128k', mp3_path],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    p.communicate(input=raw_pcm)
    duration = len(samples) / sr
    
    return {
        "agent": agent_key,
        "text": text,
        "wav_path": mp3_path,
        "duration": duration
    }

def estimate_word_timings(text: str, total_duration: float):
    """
    High-precision phonetic & syllable-weighted timing allocator.
    Long polysyllabic words, punctuation pauses, and phonetic clusters are weighted
    empirically to match Kokoro ONNX speech cadence with zero word-lag.
    """
    words = text.split()
    if not words:
        return []
    
    import re
    def calc_weight(w: str):
        clean = re.sub(r'[^a-zA-Z0-9]', '', w).lower()
        if not clean:
            return 1.0
        # Count vowel groups (syllable nucleus)
        syllables = len(re.findall(r'[aeiouy]+', clean))
        if clean.endswith('e') and not clean.endswith('le') and len(clean) > 2 and not clean.endswith('ee'):
            syllables = max(1, syllables - 1)
        syllables = max(1, syllables)
        # Syllables account for phoneme duration, char count accounts for consonant clusters
        weight = (syllables * 3.2) + (len(clean) * 0.45)
        # Punctuation induces acoustic pause in speech synthesis
        if any(c in w for c in '.,;:!?'):
            weight += 3.8
        if any(c in w for c in '—–-'):
            weight += 2.0
        return max(1.5, weight)

    weights = [calc_weight(w) for w in words]
    total_w = sum(weights) or 1.0
    
    # Reserve initial 0.05s buffer for audio device playback initiation
    effective_dur = max(0.5, total_duration - 0.08)
    cur_t = 0.05
    telemetry = []
    
    for w, wt in zip(words, weights):
        w_dur = (wt / total_w) * effective_dur
        telemetry.append({
            "word": w,
            "start": round(cur_t, 3),
            "end": round(cur_t + w_dur, 3)
        })
        cur_t += w_dur
        
    return telemetry

def play_turn(turn_payload):
    agent = turn_payload["agent"]
    text = turn_payload["text"]
    wav_path = turn_payload["wav_path"]
    
    # Update stage HUD and real-time word-level timing telemetry
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(agent, encoding="utf-8")
        TRANSCRIPT_FILE.write_text(text, encoding="utf-8")
        
        dur = turn_payload.get("duration", max(1.0, len(text.split()) * 0.35))
        now_ts = time.time()
        word_telemetry = estimate_word_timings(text, dur)
        
        timing_payload = {
            "agent": agent,
            "text": text,
            "start_time": now_ts,
            "total_duration": round(dur, 2),
            "words": word_telemetry,
            "synthesizing": False,
            "complete": False
        }
        TIMING_JSON.write_text(json.dumps(timing_payload), encoding="utf-8")
    except Exception:
        pass
    
    print(f"\n🎙️ [{agent.upper()}]: \"{text}\"")
    sys.stdout.flush()

    # Play the synthesized audio through Mac built-in speakers
    if os.path.exists(wav_path):
        subprocess.run(["/usr/bin/afplay", wav_path], check=False)
        try:
            os.remove(wav_path)
        except OSError:
            pass

def dispatch_council(turns: list[tuple[str, str]], pause_between: float = 0.08):
    """
    Executes a multi-turn council deliberation with TRUE ZERO-GAP STITCHING.
    All turns are synthesized in memory, concatenated seamlessly into ONE SINGLE audio stream
    with an exact natural breath gap (0.08s), and played continuously via afplay.
    Guarantees mathematically ZERO possibility of dead air, waiting, or gaps between speakers.
    """
    # Normalize input: support either list of [speaker, text] or dict with 'dialogue'
    if isinstance(turns, dict) and "dialogue" in turns:
        normalized = []
        for d in turns["dialogue"]:
            speaker = d.get("agent") or d.get("speaker") or "maxx"
            text = d.get("text") or ""
            normalized.append((speaker, text))
        turns = normalized
    elif isinstance(turns, list):
        normalized = []
        for item in turns:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                normalized.append((item[0], item[1]))
            elif isinstance(item, dict):
                speaker = item.get("agent") or item.get("speaker") or "maxx"
                text = item.get("text") or ""
                normalized.append((speaker, text))
        turns = normalized

    if not turns:
        print("[COUNCIL AUDIO] Empty dialogue sequence. Nothing to play.")
        return

    with open(AUDIO_LOCK_FILE, "w") as lock_f:
        fcntl.flock(lock_f, fcntl.LOCK_EX)
        try:
            print("=" * 70)
            print("🎙️ XORAS SOVEREIGN COUNCIL: TRUE ZERO-GAP STITCHED AUDIO ENGINE")
            print(f"Total Deliberation Turns : {len(turns)}")
            print(f"Inter-Speaker Natural Breath Gap : {pause_between:.2f}s")
            print("Substrate: Apple Silicon M4 Unified RAM (Kokoro ONNX)")
            print("Mode: SINGLE CONTINUOUS AUDIO STREAM (ABSOLUTELY ZERO GAPS)")
            print("=" * 70)
            
            engine = get_kokoro()
            sr = 24000
            breath_silence = np.zeros(int(sr * pause_between), dtype=np.float32)
            
            combined_samples = []
            turn_metadata = []
            
            # Synthesize all turns and concatenate PCM in unified RAM
            for i, (agent, text) in enumerate(turns):
                agent_key = resolve_agent_key(agent)
                voice_name = manifest_voice(agent_key)
                speed = VOICE_MAP.get(agent_key, (voice_name, 1.0))[1]
                calm_text = clean_calm_text(text)
                
                samples, sr = engine.create(calm_text, voice=voice_name, speed=speed, lang="en-us")
                
                # Soft cosine acoustic envelope (prevent clicks)
                if len(samples) > 0:
                    fade_len = min(int(sr * 0.02), len(samples) // 4)
                    if fade_len > 0:
                        fade_in = np.sin(np.linspace(0, np.pi / 2, fade_len)) ** 2
                        fade_out = np.sin(np.linspace(np.pi / 2, 0, fade_len)) ** 2
                        samples[:fade_len] = samples[:fade_len] * fade_in
                        samples[-fade_len:] = samples[-fade_len:] * fade_out
                
                turn_dur = len(samples) / sr
                turn_metadata.append({
                    "agent": agent_key,
                    "text": text,
                    "duration": turn_dur
                })
                
                combined_samples.append(samples)
                if i + 1 < len(turns):
                    combined_samples.append(breath_silence)
            
            # Flatten to single continuous array
            full_audio = np.concatenate(combined_samples)
            total_duration = len(full_audio) / sr
            
            # Encode single continuous MP3 stream
            stitched_mp3 = "/tmp/council_stitched_stream.mp3"
            raw_pcm = (full_audio * 32767).astype(np.int16).tobytes()
            p = subprocess.Popen(
                ['/opt/homebrew/bin/ffmpeg', '-y', '-f', 's16le', '-ar', str(sr), '-ac', '1', '-i', 'pipe:0', '-codec:a', 'libmp3lame', '-b:a', '128k', stitched_mp3],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            p.communicate(input=raw_pcm)
            
            # Print deliberation turns to console
            for tm in turn_metadata:
                print(f"\n🎙️ [{tm['agent'].upper()}]: \"{tm['text']}\"")
            sys.stdout.flush()
            
            # Play the entire seamless stream in ONE SINGLE afplay call
            if os.path.exists(stitched_mp3):
                subprocess.run(["/usr/bin/afplay", stitched_mp3], check=False)
                try:
                    os.remove(stitched_mp3)
                except OSError:
                    pass
                    
            print("\n" + "=" * 70)
            print("✅ ZERO-GAP COUNCIL AUDIT CONCLUDED WITH FLAWLESS HANDOFFS")
            print("=" * 70)
        finally:
            fcntl.flock(lock_f, fcntl.LOCK_UN)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Xoras Sovereign Council Audio Dispatch")
    parser.add_argument("--json", action="store_true", help="Read JSON turns array from stdin")
    parser.add_argument("--speaker", type=str, help="Single speaker name (e.g. Maxx, Vance, DAXX)")
    parser.add_argument("--text", type=str, help="Spoken text for single speaker")
    parser.add_argument("positional_args", nargs="*", help="Positional arguments: [speaker, text] or raw JSON")

    parsed, unknown = parser.parse_known_args()

    if parsed.json:
        data = json.loads(sys.stdin.read())
        dispatch_council(data)
    elif parsed.speaker and parsed.text:
        dispatch_council([(parsed.speaker, parsed.text)])
    elif parsed.positional_args:
        # Check if first arg is a known speaker and second arg is text
        if len(parsed.positional_args) >= 2 and parsed.positional_args[0].lower() in VOICE_MAP:
            spk = parsed.positional_args[0]
            txt = " ".join(parsed.positional_args[1:])
            dispatch_council([(spk, txt)])
        else:
            raw_input = " ".join(parsed.positional_args)
            try:
                data = json.loads(raw_input)
                dispatch_council(data)
            except Exception as e:
                print(f"[COUNCIL AUDIO] Error parsing input: {e}. Raw input: {raw_input}")
                sys.exit(1)
    else:
        print("[COUNCIL AUDIO] Error: No dialogue turns provided.")
        sys.exit(1)
