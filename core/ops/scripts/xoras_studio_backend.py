import os
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from pathlib import Path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
PRODUCTS_DIR = ROOT / "products" / "xoras_studio"
PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)
QUEUE_FILE = ROOT / "scratch" / "speech_queue.txt"
QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)

class ChatRequest(BaseModel):
    agent: str
    message: str
    context: str = ""

@app.post("/api/chat")
async def chat_with_agent(req: ChatRequest):
    # Route to local Ollama
    model = "gemma4:26b"
    if req.agent.lower() == "daxx":
        model = "qwen2.5-coder:7b"
    elif req.agent.lower() == "jarvis":
        model = "sovereign-jarvis:latest"

    system_prompt = f"You are {req.agent}, a core member of the Sovereign Lead 9 collective. The user is talking to you through the XORAS Studio IDE. Keep responses highly technical, concise, and grounded in the SOVRA architecture. Code Context: {req.context}"
    
    payload = {
        "model": model,
        "prompt": req.message,
        "system": system_prompt,
        "stream": False
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post("http://127.0.0.1:11434/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
            response_text = data.get("response", "Error: No response from model.")
            
            # Queue audio directly to the voice daemon
            with open(QUEUE_FILE, "a", encoding="utf-8") as f:
                # Basic cleaning for TTS
                clean_speech = response_text.replace("\n", " ").replace('"', '').replace("`", "")
                if len(clean_speech) > 400:
                    clean_speech = clean_speech[:400] + "... output too long for speech, see IDE panel."
                f.write(f"{req.agent.lower()} | {clean_speech}\n")
                
            return {"response": response_text, "model_used": model}
        except Exception as e:
            return {"response": f"Sovereign API Error: {str(e)}", "model_used": model}

@app.get("/", response_class=HTMLResponse)
async def serve_ide():
    index_path = PRODUCTS_DIR / "index.html"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    return "<h1>XORAS Studio UI Missing. Ensure index.html is in products/xoras_studio/</h1>"

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
