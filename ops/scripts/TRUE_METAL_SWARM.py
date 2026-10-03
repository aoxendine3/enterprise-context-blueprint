import urllib.request
import json
import concurrent.futures
import time

URL = "http://127.0.0.1:11434/api/generate"
MODEL = "llama3.2:3b"  # Fast, local, capable of parallel swarm

AGENTS = {
    "Daxx": "You are Daxx, Error Remediation Master. Analyze Computational Interference Memory for memory leak flaws.",
    "Orion": "You are Orion, Media Director. Construct the visual topology layout for a Wave Computing memory matrix.",
    "Dr. Eden Veritas": "You are Dr. Eden Veritas, Clinical Protection Invariant. Ensure the Wave computing architecture contains zero bio-resonance harm variables.",
    "Dr. Jeremy Brown": "You are Dr. Jeremy Brown. Apply rigorous scientific analysis to the phase-amplitude transformation.",
    "Clara": "You are Clara, Chief of Science. Propose the physical state mechanism for Wave computing.",
    "Vance": "You are Vance, The Falsifier. Attempt to destroy Clara's physical state mechanism.",
    "Maxx": "You are Maxx, Ops Lead. Orchestrate the throughput metrics of the wave cluster.",
    "Jarvis": "You are Jarvis, Governance AI. Ensure the swarm adheres to the 7th Layer invariants.",
    "John": "You are John, Tactical Exec. Map the quickest path to bare-metal compilation."
}

def hit_ollama(agent_name, prompt):
    data = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 100}
    }
    req = urllib.request.Request(URL, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
    start = time.time()
    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read())
        elapsed = time.time() - start
        print(f"\033[92m[{agent_name}]\033[0m Local inference complete ({elapsed:.2f}s). Result logged.")
        return {"agent": agent_name, "time": elapsed, "response": result.get("response", "").strip()}
    except Exception as e:
        print(f"\033[91m[{agent_name}]\033[0m Failed to hit local model: {e}")
        return None

if __name__ == "__main__":
    print(f"=== INITIATING BARE-METAL 9-AGENT SWARM ON OLLAMA ({MODEL}) ===")
    start_all = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=9) as executor:
        futures = []
        for name, prompt in AGENTS.items():
            futures.append(executor.submit(hit_ollama, name, prompt))
        
        with open("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/journals/true_metal_swarm.jsonl", "a") as f:
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res:
                    f.write(json.dumps(res) + "\n")
    print(f"=== SWARM COMPLETE IN {time.time()-start_all:.2f}s ===")
