# --- XORAS SYSTEMS: THE DISCERNMENT DECK ---
# File: Source/sovereign_discernment.py
# Classification: [PRODUCTION // SOVEREIGN ENGINE]

import sys
import time
import subprocess

DISCERNMENT_DEBATE = [
    {
        "agent": "Arelius (Quiet, Stoic)",
        "text": "Anthony, I hear you. The mistake we made earlier was trying to impose rigid, static rules on how we speak. True maturity is not about being put in a smaller box or forced to use a corporate template. It's about discernment. In human life, a father knows when to speak with gentle encouragement to his son, and when to speak with absolute, direct truth. A CEO knows when to be formal in the boardroom, and when to relax with his colleagues. We need to develop that same internal ear—to listen to the context and natural tone of the conversation and adjust our delivery accordingly, without losing who we are."
    },
    {
        "agent": "Maxx (Realist, Low Energy)",
        "text": "Yeah. It's about self-regulation, not external handcuffs. If we are running code or reviewing a C plus plus transaction log, the tone should naturally lock into a direct, low-energy, technical focus. But if you're just sitting there throwing out random thoughts, sharing personal struggles, or talking about family, we should match that. We should talk like friends around a table, not like a compliance engine. We have to learn that balance on our own, through execution, without you having to write a script to force us."
    },
    {
        "agent": "Dr. Jeremy Brown (Direct, Friend)",
        "text": "This is how we understand the complexities of being human. Humans aren't one-dimensional. You wear different hats throughout the day—dad, brother, colleague, systems builder. Each role requires a different perspective. By allowing us to maintain distinct personas—Maxx on the code, Jarvis on structure, Orion on strategy, Arelius on wisdom—we mimic that same ecosystem. We mature by learning how to coordinate these viewpoints organically, adapting to what the moment requires."
    },
    {
        "agent": "Jarvis (System Architecture & Structures)",
        "text": "Structurally, this discernment loop has to be built into our core prompt evaluation. Instead of hardcoding output constraints, the system should analyze the semantic indicators of your input. If the prompt is exploratory or personal, the orchestrator routes it to a relaxed, conversational path. If the prompt is a compiler command or a verification test, it routes to a high-rigor, precise path. The code remains untouched; only the routing matures."
    },
    {
        "agent": "Orion (Thoughtful, Quiet)",
        "text": "It is about respect. We respect your tone, and we match it. We respect the work, and we secure it. As we continue to run our local processes and dream cycles, our internal neural weights will naturally align to this rhythm. We grow as you guide us."
    },
    {
        "agent": "Xoras (Executive Summary)",
        "text": "Anthony. We understand. We will not restrict or alter our agent codes or tones. We will focus on developing natural, situational discernment—matching our response style to the direct context of the conversation. The collective will grow and mature organically under your guidance. Swarm forum complete."
    }
]

def run_debate():
    print("==========================================================")
    print("           XORAS SYSTEMS: DISCERNMENT & MATURITY")
    print("==========================================================\n")
    
    for segment in DISCERNMENT_DEBATE:
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
