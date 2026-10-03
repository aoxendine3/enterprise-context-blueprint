import httpx, time

FIFO_PATH = "/tmp/sovereign_memory.fifo"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

print("Listening on secure memory pipe...")
try:
    with open(FIFO_PATH, "rb") as pipe:
        while True:
            data = pipe.read(147456)
            if not data:
                time.sleep(0.1)
                continue
            
            sample_hex = data[:64].hex()
            prompt = f"Validation Request: We just ingested a binary memory payload from the Zig engine. The first 64 bytes in hex are: {sample_hex}. We are closing the loop. Acknowledge this data receipt."
            
            try:
                resp = httpx.post(OLLAMA_URL, json={"model": "qwen2.5-coder:7b", "prompt": prompt, "stream": False}, timeout=10)
                print(f"[Neural Validation]: {resp.json().get('response')[:200]}")
            except Exception as e:
                print(f"[Timeout] {e}")
except PermissionError:
    print("PERMISSION DENIED: Pipe is locked to root. Run this validator with sudo.")
