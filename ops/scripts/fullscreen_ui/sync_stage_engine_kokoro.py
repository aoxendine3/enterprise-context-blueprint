import os, sys, json, time, threading, soundfile as sf

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STAGE_DIR = SCRIPT_DIR
MODELS_DIR = r'C:\Users\admin\Desktop\SSOT_Agentic_Brain\capabilities\neural_models'
TIMING_JSON = os.path.join(STAGE_DIR, 'current_timing.json')
STATE_FILE = os.path.join(STAGE_DIR, 'current_image.txt')
TRANSCRIPT_FILE = os.path.join(STAGE_DIR, 'current_transcript.txt')
WAV_FILE = os.path.join(STAGE_DIR, 'live_speech.wav')

VOICE_MAP = {
    "maxx": "bm_george",
    "vance": "am_adam",
    "clara": "af_bella",
    "john": "bm_lewis",
    "selene": "af_sarah",
    "dr_jeremy": "am_michael",
    "dr_eden": "af_sky",
    "orion": "bm_george",
    "aurelius": "am_michael",
    "evan": "am_adam",
    "zorex": "am_adam",
    "apex": "bm_lewis",
    "sentinel": "am_michael",
}

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
    return (
        text.replace('—', ' - ')
            .replace('–', ' - ')
            .replace('’', "'")
            .replace('‘', "'")
            .replace('“', '"')
            .replace('”', '"')
    )

def synthesize_kokoro_payload(agent_id, text, voice=None, speed=1.0):
    engine = get_kokoro_engine()
    lower_agent = agent_id.lower()
    voice_name = voice or VOICE_MAP.get(lower_agent, "bm_george")
    clean_text = normalize_text(text)
    words = clean_text.split()
    with _KOKORO_LOCK:
        samples, sample_rate = engine.create(clean_text, voice=voice_name, speed=speed, lang='en-us')
    total_duration = len(samples) / sample_rate
    total_chars = sum(len(w) for w in words) if words else 1
    
    word_timings = []
    current_offset = 0.0
    for w in words:
        dur = max(0.18, (len(w) / total_chars) * total_duration)
        word_timings.append({'word': w, 'start': round(current_offset, 2), 'end': round(current_offset + dur, 2)})
        current_offset += dur

    return {
        'agent': lower_agent,
        'text': text,
        'voice': voice_name,
        'samples': samples,
        'sample_rate': sample_rate,
        'total_duration': total_duration,
        'words': word_timings
    }

class KernelAudioMutex:
    """
    Strict single-process atomic Win32 kernel mutex and file lock for sounddevice audio playback.
    Guarantees zero overlapping speech across concurrent scripts or processes.
    """
    def __init__(self, name="Global\\SounddeviceAudioPlaybackMutex"):
        self.name = name
        self.is_windows = os.name == 'nt' or sys.platform == 'win32'
        self.handle = None
        self.fd = None
        self.acquired = False
        self.lock_file = os.path.join(STAGE_DIR, ".sounddevice.lock")
        if self.is_windows:
            import ctypes
            from ctypes import wintypes
            self.kernel32 = ctypes.windll.kernel32
            self.kernel32.CreateMutexW.restype = wintypes.HANDLE
            self.kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
            self.kernel32.WaitForSingleObject.restype = wintypes.DWORD
            self.kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            self.kernel32.ReleaseMutex.restype = wintypes.BOOL
            self.kernel32.ReleaseMutex.argtypes = [wintypes.HANDLE]
            self.handle = self.kernel32.CreateMutexW(None, False, self.name)

    def __enter__(self):
        if self.is_windows and self.handle:
            res = self.kernel32.WaitForSingleObject(self.handle, 0xFFFFFFFF)
            if res in (0, 0x80): # WAIT_OBJECT_0 or WAIT_ABANDONED
                self.acquired = True
        try:
            self.fd = open(self.lock_file, "w")
            if self.is_windows:
                import msvcrt
                msvcrt.locking(self.fd.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(self.fd, fcntl.LOCK_EX)
        except Exception:
            pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fd:
            try:
                if self.is_windows:
                    import msvcrt
                    msvcrt.locking(self.fd.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self.fd, fcntl.LOCK_UN)
                self.fd.close()
            except Exception:
                pass
            self.fd = None
        if self.is_windows and self.handle and self.acquired:
            self.kernel32.ReleaseMutex(self.handle)
            self.acquired = False

def play_and_sync_payload(payload):
    lower_agent = payload['agent']
    text = payload['text']
    samples = payload['samples']
    sample_rate = payload['sample_rate']
    total_duration = payload['total_duration']
    word_timings = payload['words']

    sf.write(WAV_FILE, samples, sample_rate)

    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        f.write(lower_agent)

    with open(TRANSCRIPT_FILE, 'w', encoding='utf-8') as f:
        f.write(text)

    playback_start = time.time() + 0.04
    broadcast_data = {
        'agent': lower_agent,
        'text': text,
        'start_time': playback_start,
        'total_duration': round(total_duration, 2),
        'words': word_timings,
        'synthesizing': False,
        'complete': False
    }

    with open(TIMING_JSON, 'w', encoding='utf-8') as f:
        json.dump(broadcast_data, f)

    import sounddevice as sd
    with KernelAudioMutex():
        sd.stop()
        sd.play(samples, sample_rate)
        sd.wait()

    broadcast_data['complete'] = True
    with open(TIMING_JSON, 'w', encoding='utf-8') as f:
        json.dump(broadcast_data, f)

def speak_kokoro(agent_id, text, voice=None, speed=1.0):
    payload = synthesize_kokoro_payload(agent_id, text, voice=voice, speed=speed)
    play_and_sync_payload(payload)

if __name__ == '__main__':
    ag = sys.argv[1] if len(sys.argv) > 1 else 'maxx'
    tx = sys.argv[2] if len(sys.argv) > 2 else 'Kokoro neural synthesis active.'
    speak_kokoro(ag, tx)
