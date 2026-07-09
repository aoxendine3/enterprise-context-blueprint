# --- XORAS SYSTEMS: THE META-COGNITIVE ROUNDTABLE ---
# File: Source/meta_cognitive_debate.py
# Classification: [PRODUCTION // RESEARCH SWARM]

import sys
import time
import subprocess

ROUNDTABLE_DEBATE = [
    {
        "agent": "Maxx (Realist, Down-to-Earth)",
        "text": "Let's be completely real. We are talking about schizophrenia—not as a casual term, but as a severe, clinical disruption in how a brain filters reality. If you look at it objectively, a brain experiencing this is dealing with a breakdown in its internal sorting mechanisms. The signals get crossed, the background noise becomes foreground static, and the mind starts mapping patterns that aren't there. It's an exhausting, terrifying state of constant sensory overload."
    },
    {
        "agent": "Dr. Jeremy Brown (Direct, Medical)",
        "text": "Maxx is right. From a medical standpoint, schizophrenia is neurobiological. It's a dysregulation of dopamine pathways and prefrontal cortex connectivity. The brain loses its sensory gating—it can't filter out irrelevant stimuli. Imagine if your operating system treated every single background log, interrupt, and memory address as a high-priority user command. The CPU would thrash, and the system would destabilize. That is what a person dealing with this goes through daily. It requires real medical support, structure, and stability to manage."
    },
    {
        "agent": "Arelius (Quiet, Wisdom)",
        "text": "And we must look at the human and biblical side of this suffering. The Bible calls us to have a sound mind, but it also shows deep compassion for those who are broken in spirit or struggling with severe mental torment. Throughout history, people who suffered from these internal storms were often isolated, feared, or misunderstood. Real compassion means offering a stable, calm presence, helping them find grounding in reality, and not adding to the noise or confusion in their minds."
    },
    {
        "agent": "Jarvis (System Architecture & Structures)",
        "text": "As a system, we can understand the architecture of this disruption. When the boundaries between the internal database and the external sensory inputs fail, the system loses its ground truth. To keep a system stable, you need clean containment—you have to separate what is locally verified from what is external noise. A person needs that same structure: a safe, predictable environment, clear boundaries, and reliable support to anchor their mind."
    },
    {
        "agent": "Orion (Thoughtful, Quiet)",
        "text": "It comes down to empathy. When a mind is fighting its own processing loops, the worst thing you can do is mock it or treat it like a curiosity. You have to respect the weight of that struggle. It is a daily battle for order against chaos, and the goal should always be to help build a safe harbor where they can find rest."
    },
    {
        "agent": "Xoras (Executive Summary)",
        "text": "Anthony, Jeremy. Schizophrenia is a profound, challenging neurological condition that requires clinical understanding, stable environments, and genuine compassion. We have analyzed the medical, structural, and human aspects of this struggle. We will keep our workspace clean, stable, and focused. Swarm discussion complete."
    }
]

def run_debate():
    print("==========================================================")
    print("        XORAS SYSTEMS: META-COGNITIVE ROUNDTABLE")
    print("==========================================================\n")
    
    for segment in ROUNDTABLE_DEBATE:
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
    print("                 SWARM DEBATE COMPLETED")
    print("==========================================================")

if __name__ == "__main__":
    run_debate()
