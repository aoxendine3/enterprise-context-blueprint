import urllib.request
import json
import sys
import subprocess
import time

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "llama3.2:3b"

def query_agent(agent_name, role_prompt, context):
    prompt = f"You are {agent_name}. {role_prompt}\n\nThe current conversation:\n{context}\n\nRespond as {agent_name} in 2-3 short, natural sentences. Do NOT use emojis, markdown, or asterisks. Speak directly and naturally as your persona."
    
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    req = urllib.request.Request(OLLAMA_URL, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['response'].strip().replace('"', '').replace('\n', ' ')
    except Exception as e:
        return f"I am unable to connect to my cognitive core. {e}"

def main():
    print("Initiating Ollama-driven Sovereign Triad Deliberation...")
    
    agents = [
        ("maxx", "You are the seasoned Systems Architect. You talk about how the 128-byte block was fast but forced the NVMe hard drive into inefficient read-modify-write loops because hard drives natively write in 512-byte chunks."),
        ("clara", "You are the Chief of Science. You follow up on Maxx, explaining the mathematical perfection that the massive 18,432-dimensional Rust AI vector divides flawlessly into the new 512-byte blocks without a single wasted byte."),
        ("vance", "You are the Falsifier. You talk about how you threw this new 512-byte architecture into the Sovereign Dojo cage to try and break it, but it dominated the 14-Gate Blackbox Gauntlet with zero memory bleed and an impossible 0.84% cache miss ratio."),
        ("jarvis", "You are the Governance AI. You conclude by officially declaring the architecture certified as GOLDEN-980, sealing it as the new absolute atomic unit of the collective.")
    ]
    
    context = "Topic: The epic resonance of the 512-byte HexCell and the 18,432D vector.\n"
    turns = []
    
    for agent, role in agents:
        print(f"Querying {agent.upper()} via Ollama ({MODEL})...")
        response_text = query_agent(agent, role, context)
        print(f"{agent}: {response_text}\n")
        context += f"{agent.upper()}: {response_text}\n"
        turns.append({"agent": agent, "text": response_text})
        
    print("Dispatching generated thoughts to the Media Director...")
    
    # Save to temp JSON
    with open('/tmp/ollama_story.json', 'w') as f:
        json.dump(turns, f)
        
    # Execute Media Director
    subprocess.run(["python3", "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/media_director_agent.py", "maxx", json.dumps(turns)])

if __name__ == "__main__":
    main()
