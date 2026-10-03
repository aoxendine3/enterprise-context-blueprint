import os, time, httpx, random

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
CORPUS_DIR = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/tri_brain/corpus"

TOPICS = [
    "Formal mathematical proofs in Non-Euclidean geometry, algebraic topology, and prime number sieves.",
    "Advanced linguistic syntax trees, semantic translation layers, and universal grammar.",
    "Agentic communication protocols, high-stakes negotiation etiquette, and board-level articulation.",
    "Quantum physics, wave-function collapse mechanics, and tensor calculus for general relativity.",
    "Ancient historical cryptography, Sumerian numerical systems, and hieroglyphic dimensional mapping."
]

print("Initiating Hellacious Ingestion Swarm...")

count = 0
# Run until killed
while True:
    topic = random.choice(TOPICS)
    prompt = f"Generate an extremely dense, highly advanced, and factually bulletproof academic breakdown regarding: {topic}. Output pure knowledge, advanced formulas, and strict protocol rules. Do not hallucinate."
    
    try:
        resp = httpx.post(OLLAMA_URL, json={"model": "qwen2.5-coder:7b", "prompt": prompt, "stream": False}, timeout=180)
        data = resp.json().get("response", "")
        
        if data:
            with open(f"{CORPUS_DIR}/corpus_block_{count}.md", "w", encoding="utf-8") as f:
                f.write(f"# INGESTION DOMAIN: {topic}\n\n{data}")
            print(f"Successfully Ingested Block {count} into Sovereign Corpus.")
            count += 1
    except Exception as e:
        print(f"Error on block {count}: {e}")
        time.sleep(5)
