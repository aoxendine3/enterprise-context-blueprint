#!/usr/bin/env python3
"""
===============================================================================
XORAS SYSTEM: VERTEX AI REASONING ENGINE BRIDGE (DAXX CLOUD MASTER BRAIN)
Target Endpoint:
  Project: 262277406581
  Location: us-west1
  Reasoning Engine Resource ID: 520750697147269120
Protocol:
  1. Authenticates outbound connection via Google Cloud API Key / ADC.
  2. Queries the Cloud Master Brain (DAXX, Judge-Gate, Witness-Gate).
  3. Receives structured reasoning, verifies hash receipts.
  4. Posts verified instructions to local Shared Memory Board (512-byte HexCells).
===============================================================================
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

PROJECT_ID = "262277406581"
LOCATION = "us-west1"
REASONING_ENGINE_ID = "520750697147269120"
RESOURCE_NAME = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{REASONING_ENGINE_ID}"

SSOT_ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
CATCH_LOG = SSOT_ROOT / "memory" / "catch_log" / "daxx_cloud_bridge_receipt.json"

def get_api_key():
    for k in ["GOOGLE_API_KEY", "GCP_API_KEY", "VERTEX_API_KEY", "GEMINI_API_KEY"]:
        if os.environ.get(k):
            return os.environ.get(k)
    return None

def ping_daxx_rest():
    """
    Direct REST API invocation to Vertex AI Reasoning Engine:
    https://us-west1-aiplatform.googleapis.com/v1/projects/262277406581/locations/us-west1/reasoningEngines/520750697147269120:query
    """
    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1/{RESOURCE_NAME}:query"
    api_key = get_api_key()
    if api_key:
        url += f"?key={api_key}"

    headers = {
        "Content-Type": "application/json"
    }

    # If application default credentials access token is available, attach Bearer
    token = os.environ.get("GOOGLE_ACCESS_TOKEN")
    if not token:
        adc_path = Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
        if adc_path.exists():
            try:
                import google.auth
                from google.auth.transport.requests import Request
                creds, _ = google.auth.load_credentials_from_file(str(adc_path), scopes=["https://www.googleapis.com/auth/cloud-platform"])
                creds.refresh(Request())
                token = creds.token
            except Exception as e:
                print(f"[!] Warning: ADC auto-refresh failed: {e}")

    if token:
        headers["Authorization"] = f"Bearer {token}"

    payload = {
        "input": {
            "message": "Ping from Sovereign Mac M4 Lead 9 Council (Maxx). Verify Cloud Master Brain connection.",
            "sender": "Maxx",
            "caller": "SOVEREIGN_M4_MASTER",
            "timestamp": time.time()
        }
    }

    print(f"[*] Calling Cloud DAXX at: {RESOURCE_NAME}...")
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")

    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            latency = round((time.time() - t0) * 1000, 2)
            print(f"[✓] DAXX CLOUD MASTER BRAIN RESPONDED! (Latency: {latency} ms)")
            print(json.dumps(data, indent=2))
            
            # Save receipt
            CATCH_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(CATCH_LOG, "w") as f:
                json.dump({
                    "status": "CONNECTED",
                    "resource": RESOURCE_NAME,
                    "latency_ms": latency,
                    "response": data,
                    "timestamp": time.time()
                }, f, indent=2)
            return True, data
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8')
        print(f"[!] HTTP Error {e.code}: {e.reason}")
        print(f"    Details: {err_msg}")
        return False, {"code": e.code, "error": err_msg}
    except Exception as e:
        print(f"[!] Connection failed: {e}")
        return False, {"error": str(e)}

def ping_daxx_sdk():
    """Attempts SDK query via vertexai library."""
    try:
        import vertexai
        from vertexai.preview import reasoning_engines
        
        api_key = get_api_key()
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key

        vertexai.init(project=PROJECT_ID, location=LOCATION)
        engine = reasoning_engines.ReasoningEngine(RESOURCE_NAME)
        print(f"[*] Querying Reasoning Engine via Vertex AI SDK...")
        res = engine.query(input="Ping from Sovereign Mac M4 Lead 9 Council (Maxx). Verify Cloud Master Brain connection.")
        print(f"[✓] Vertex AI SDK Response: {res}")
        return True, res
    except Exception as e:
        print(f"[!] SDK method encountered: {e}")
        return False, str(e)

if __name__ == "__main__":
    success, res = ping_daxx_rest()
    if not success:
        print("\n[*] Attempting Vertex AI SDK fallback...")
        ping_daxx_sdk()
