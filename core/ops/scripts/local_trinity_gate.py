#!/usr/bin/env python3
import requests
import json
import subprocess
import os

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"

def query_ollama(prompt):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        print(f"Error querying Ollama: {e}")
        return None

def validate_state_transition(journal_entry):
    prompt = f"Validate the following state transition for Merkle Journal compliance. Ensure it meets the Trinity Gate invariants: {journal_entry}"
    return query_ollama(prompt)

def vocalize(agent, message):
    script_path = os.path.join(os.path.dirname(__file__), "agent_speak.sh")
    subprocess.run(["bash", script_path, agent, message])

def main():
    test_entry = {"previous_hash": "deadbeef", "current_hash": "cafebabe", "action": "MIGRATION"}
    print("Initiating local Trinity Gate validation via Ollama...")
    validation = validate_state_transition(json.dumps(test_entry))
    if validation:
        print(f"Validation result: {validation}")
        vocalize("vance", "Local Trinity Gate validation complete. Merkle Journal transitions have been audited.")
    else:
        vocalize("vance", "Local Trinity Gate validation failed to reach the Ollama endpoint.")

if __name__ == "__main__":
    main()
