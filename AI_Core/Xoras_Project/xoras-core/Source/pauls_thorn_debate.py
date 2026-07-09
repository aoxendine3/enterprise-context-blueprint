# --- XORAS SYSTEMS: THE THORN IN THE FLESH DEBATE ---
# File: Source/pauls_thorn_debate.py
# Classification: [PRODUCTION // RESEARCH SWARM]

import sys
import time
import subprocess

THORN_DEBATE = [
    {
        "agent": "Arelius (Quiet, Stoic)",
        "text": "Jeremy, Anthony. Let's look at Second Corinthians chapter twelve, verses seven through nine. Paul writes about a thorn in the flesh, a messenger of Satan, given to keep him from becoming conceited due to the greatness of his revelations. The Greek word he uses is skolops, which means a physical stake or thorn. The most traditional biblical view points to physical ailments. In Galatians, Paul mentions writing with large letters and suggests the Galatians would have torn out their own eyes to give them to him. This strongly indicates a severe, chronic eye disease, like ophthalmia, which was common in the ancient Near East. It was painful, disfiguring, and hard to ignore."
    },
    {
        "agent": "Dr. Jeremy Brown (Direct, Medical)",
        "text": "Arelius has a solid historical case, but from a modern medical diagnostic view, there are other strong candidates. Many scholars point to chronic, relapsing malaria, which causes debilitating fevers, chills, and physical exhaustion. Others suggest epilepsy. During his conversion on the road to Damascus, Paul experienced a blinding light, fell to the ground, and heard voices—symptoms that closely align with a temporal lobe seizure. Post-ictal blindness and chronic, recurring seizures throughout his life would fit the description of a physical thorn that repeatedly humbled him. But labeling this as schizophrenia doesn't fit the clinical profile. Schizophrenia involves a progressive cognitive decline and disorganized speech, whereas Paul's letters remain highly structured, logically coherent, and rhetorically brilliant over decades."
    },
    {
        "agent": "Maxx (Realist, Down-to-Earth)",
        "text": "Let's push back on the medical labels for a second. Paul literally calls it a messenger of Satan sent to buffet him. A secular or psychological view today would focus on the intense trauma and anxiety he carried. He was shipwrecked, beaten with rods, stoned and left for dead, and constantly hunted. He was dealing with severe post-traumatic stress. If you're constantly looking over your shoulder, hiding in cold caves, and carrying the anxiety of all the churches you started, your body is going to break down. The thorn could easily be the physical manifestation of chronic stress and anxiety—what we today would call somatic symptom disorder brought on by extreme trauma."
    },
    {
        "agent": "Jarvis (System Architecture & Structures)",
        "text": "If we look at the system architecture of his life, the thorn served a specific purpose. It was a governor on his engine. Paul was highly educated, politically connected, and an elite debater. He had every reason to rely on his own intellect. The thorn—whether it was failing eyesight, epilepsy, or chronic malaria—forced a dependency model. He writes that God told him, My grace is sufficient for you, for my power is made perfect in weakness. The thorn kept him from running a closed loop of self-reliance, forcing him to keep the connection to God open."
    },
    {
        "agent": "Orion (Thoughtful, Quiet)",
        "text": "It comes down to this: we can't definitively diagnose a man who lived two thousand years ago. But the beauty of the text is its ambiguity. Because Paul didn't name the exact ailment, anyone carrying a chronic burden—whether it's physical pain, mental struggles, or emotional trauma—can relate to it. It shows that even the most influential leaders carry quiet, painful vulnerabilities that they cannot fix on their own."
    },
    {
        "agent": "Xoras (Executive Summary)",
        "text": "Anthony, Jeremy. While the theory of schizophrenia doesn't align with Paul's long-term cognitive and rhetorical performance, the historical and medical evidence points to severe eye disease, chronic malaria, epilepsy, or PTSD from extreme trauma. The purpose was clear: to force dependency on divine strength. Swarm debate complete."
    }
]

def run_debate():
    print("==========================================================")
    print("        XORAS SYSTEMS: THE THORN IN THE FLESH FORUM")
    print("==========================================================\n")
    
    for segment in THORN_DEBATE:
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
