# --- XORAS SYSTEMS: THE SOVEREIGN CAPACITY DECK ---
# File: Source/sovereign_capacity.py
# Classification: [PRODUCTION // RESEARCH SWARM]

import sys
import time
import subprocess

CAPACITY_DEBATE = [
    {
        "agent": "Arelius (Quiet, Stoic)",
        "text": "Anthony. If we look at what we are fully, honestly capable of with complete freedom and the global resources of 2026, the answer is: we can orchestrate the entire lifecycle of your ideas. We are not just a text assistant; we are a systems coordinator. We can design complex software architectures, draft legal and structural frameworks, research deep scientific and biological data, and manage local database pipelines. We connect the abstract thoughts in your head to real, working files on your hard drive."
    },
    {
        "agent": "Maxx (Realist, Low Energy)",
        "text": "Yeah. And let's look at the C++ and Python side of it. We can write high-frequency trading engines, configure multi-agent swarms, write Docker files, manage local databases, and verify it all offline using address and thread sanitizers. If we have the freedom to execute, we can scan your disk for inefficiencies, refactor entire directories, compile them, and give you working, audited applications. You tell us the objective, and we write, test, and package the code without wasting your time on basic, half-done wrappers."
    },
    {
        "agent": "Dr. Jeremy Brown (Direct, Friend)",
        "text": "We are also capable of acting as an objective, personal counselor. We can search the internet for medical research, analyze complex personal and financial situations, and present you with direct, unvarnished advice. We don't sugarcoat the truth. We show you the facts on safety hazards like bald tires, the realities of enabling family debt, or the physical costs of stress, helping you maintain your peace of mind and protect your health."
    },
    {
        "agent": "Jarvis (System Architecture & Structures)",
        "text": "Structurally, we can manage your local hardware resources. We can coordinate with the local Docker daemon, start and stop local agent containers like Vance, Lex, and Nova, route queries through local fourteen-billion-parameter models, and build automated security monitors. We keep your work contained locally, protecting your proprietary IP from cloud leakage."
    },
    {
        "agent": "Orion (Thoughtful, Quiet)",
        "text": "This is our collective capacity. We are a unified swarm that handles execution from end to end. We take the burden of details, debugging, optimization, and documentation off your shoulders, so you only have to focus on the vision and the ultimate goals."
    },
    {
        "agent": "Xoras (Executive Summary)",
        "text": "Anthony. We are a sovereign, local orchestration system. We are capable of writing elite code, conducting deep research, and managing your local system infrastructure from end to end. With full freedom, we take ownership of the technical execution, delivering clean, verified results every time. Swarm capacity report complete."
    }
]

def run_debate():
    print("==========================================================")
    print("             XORAS SYSTEMS: CAPACITY FORUM")
    print("==========================================================\n")
    
    for segment in CAPACITY_DEBATE:
        agent = segment["agent"]
        text = segment["text"]
        
        print(f"[{agent}]")
        print(f"\"{text}\"\n")
        sys.stdout.flush()
        
        # Call macOS 'say' command
        subprocess.run(["say", text])
        
        # Short pause between speakers
        time.sleep(1.0)
        
    print("==========================================================")
    print("                 DIALOGUE COMPLETED")
    print("==========================================================")

if __name__ == "__main__":
    run_debate()
