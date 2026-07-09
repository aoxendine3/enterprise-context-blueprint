import os
import json
import urllib.request
import urllib.error
import asyncio

ENV_PATH = os.path.join(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, 'r') as f:
        for line in f:
            if line.startswith('XAI_API_KEY='):
                os.environ['XAI_API_KEY'] = line.strip().split('=', 1)[1]

XAI_API_KEY = os.environ.get("XAI_API_KEY")
XAI_API_URL = "https://api.x.ai/v1/chat/completions"


def chat_with_grok_sync(messages):
    use_fallback = False
    error_detail = ""

    if not XAI_API_KEY:
        use_fallback = True
        error_detail = "XAI_API_KEY missing"
    else:
        data = {
            "model": "grok-2-latest",
            "messages": messages,
            "temperature": 0.7,
            "stream": False
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {XAI_API_KEY}"
        }

        req = urllib.request.Request(XAI_API_URL, data=json.dumps(
            data).encode('utf-8'), headers=headers, method='POST')

        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result['choices'][0]['message']['content']
        except urllib.error.HTTPError as e:
            error_detail = f"HTTP {e.code}: {e.read().decode('utf-8')}"
            use_fallback = True
        except Exception as e:
            error_detail = str(e)
            use_fallback = True

    if use_fallback:
        print(
            f"[xoras_grok_client] Grok call failed ({error_detail}). Falling back to local Ollama (qwen2.5-coder:1.5b)...")
        ollama_url = "http://192.168.1.133:11434/api/chat"
        ollama_data = {
            "model": "qwen2.5-coder:1.5b",
            "messages": messages,
            "stream": False
        }
        req_ollama = urllib.request.Request(
            ollama_url,
            data=json.dumps(ollama_data).encode('utf-8'),
            headers={"Content-Type": "application/json"},
            method='POST'
        )
        try:
            with urllib.request.urlopen(req_ollama) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result['message']['content']
        except Exception as e:
            return f"[ERROR] Both Grok and local Ollama fallback failed. Grok error: {error_detail}. Ollama error: {str(e)}"


async def async_chat_with_grok(messages):
    loop = asyncio.get_event_loop()
    # Run the synchronous urllib request in a background thread to avoid blocking the asyncio event loop
    return await loop.run_in_executor(None, chat_with_grok_sync, messages)
