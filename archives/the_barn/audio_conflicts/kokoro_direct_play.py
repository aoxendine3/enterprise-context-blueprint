import os, sys, json, soundfile as sf

text = sys.argv[1] if len(sys.argv) > 1 else "Testing Kokoro Audio"
voice = sys.argv[2] if len(sys.argv) > 2 else "am_michael" # Dr. Jeremy Brown's original Kokoro voice key

MODELS_DIR = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/capabilities/neural_models"
model_path = os.path.join(MODELS_DIR, "kokoro-v1.0.onnx")
voices_path = os.path.join(MODELS_DIR, "voices.bin")
wav_out = "/tmp/dr_jeremy_speech.wav"

from kokoro_onnx import Kokoro
engine = Kokoro(model_path, voices_path)
samples, sample_rate = engine.create(text, voice=voice, speed=1.0, lang="en-us")

sf.write(wav_out, samples, sample_rate)
os.system(f"afplay '{wav_out}'")
