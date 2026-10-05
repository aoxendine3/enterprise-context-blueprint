import os, time, datetime, subprocess, httpx

# Target 3 hours and 5 minutes from now (aligns with 8:30 PM)
TARGET_END_TIME = datetime.datetime.now() + datetime.timedelta(hours=3, minutes=5)
REPORT_FILE = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/docs/audits/EXPONENTIAL_TESTING_RESULTS.md"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

DOMAINS = [
    "Advanced Mathematics and Non-Euclidean Geometry",
    "Ancient History, Numerology, and Artifacts",
    "Hieroglyphics and Ancient Pattern Recognition",
    "Modern Physics and Quantum Mechanics",
    "Holographic Dimensional Structures and GHRR Manifolds"
]

def ask_ollama(prompt):
    try:
        resp = httpx.post(OLLAMA_URL, json={"model": "qwen2.5-coder:7b", "prompt": prompt, "stream": False}, timeout=180)
        return resp.json().get("response", "Model Timeout.")
    except Exception as e:
        return f"Error: {e}"

os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
with open(REPORT_FILE, "w", encoding="utf-8") as f:
    f.write("# EXPONENTIAL TESTING & TRAINING REPORT\n")
    f.write(f"**Start:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"**Target End:** {TARGET_END_TIME.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

cycle = 1
while datetime.datetime.now() < TARGET_END_TIME:
    for domain in DOMAINS:
        if datetime.datetime.now() >= TARGET_END_TIME:
            break
            
        with open(REPORT_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n## CYCLE {cycle}: STRESS TESTING [{domain}]\n")
            f.write(f"**Timestamp:** {datetime.datetime.now().strftime('%H:%M:%S')}\n\n")
            
        # 1. Synthesize Test
        synth_prompt = f"Generate an exponential stress test combining Sovereign Memory Architecture with {domain}. Push the theoretical boundaries to test system logic."
        test_data = ask_ollama(synth_prompt)
        
        # 2. Evaluate Memory Retention
        eval_prompt = f"Evaluate the following synthetic data for logical coherence and memory drift within a strict hardware memory constraint. How can we make this better? Data: {test_data[:1500]}"
        eval_data = ask_ollama(eval_prompt)
        
        with open(REPORT_FILE, "a", encoding="utf-8") as f:
            f.write("### Synthetic Generation\n")
            f.write(f"{test_data}\n\n")
            f.write("### Memory Evaluation & Optimization Strategy\n")
            f.write(f"{eval_data}\n\n")
            f.write("---\n")
            
        # Sleep for a fraction of the time to pace out the 3 hours
        # 5 domains, we want to run maybe 10 full cycles over 3 hours. 
        # 180 mins / 10 cycles = 18 mins per cycle = 3.6 mins per domain
        time.sleep(210) 
    cycle += 1

with open(REPORT_FILE, "a", encoding="utf-8") as f:
    f.write(f"\n## EXPONENTIAL TESTING COMPLETE at {datetime.datetime.now().strftime('%H:%M:%S')}\n")
