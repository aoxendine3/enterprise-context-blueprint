#!/usr/bin/env python3
import subprocess
import os

def main():
    title = "Multi-Turn Agentic Context Decay & State Pollution: Benchmarking 18,432-D Poincaré Memory vs Gemini 3.5 & Gemma-4"
    tags = "devchallenge, kagglechallenge, ai, machinelearning"
    
    post_path = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/docs/plans/DEV_KAGGLE_BENCHMARK_POST_READY.md"
    with open(post_path, "r", encoding="utf-8") as f:
        full_text = f.read()
        
    if full_text.startswith("---"):
        parts = full_text.split("---", 2)
        body = parts[2].strip() if len(parts) >= 3 else full_text
    else:
        body = full_text

    # Copy pure body markdown to system clipboard
    p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
    p.communicate(input=body.encode("utf-8"))
    
    print("=" * 75)
    print("KAGGLE BENCHMARKING CHALLENGE: SUBMISSION COMPONENTS")
    print("=" * 75)
    print("\n[TITLE FIELD COPY]:")
    print(title)
    print("\n[TAGS FIELD COPY]:")
    print(tags)
    print("\n[BODY MARKDOWN] -> Loaded into macOS System Clipboard (pbcopy)!")
    print(f"Total Body Character Count: {len(body)} chars")
    print("=" * 75)

if __name__ == "__main__":
    main()
