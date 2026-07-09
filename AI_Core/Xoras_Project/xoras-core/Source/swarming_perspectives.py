# --- XORAS SYSTEMS: MULTI-PERSPECTIVE SWARM DEBATE ---
# File: Source/swarming_perspectives.py
# Classification: [PRODUCTION // RESEARCH SWARM]

import sys
import time
import subprocess

PERSPECTIVE_DEBATE = [
    {
        "agent": "Arelius (Biblical Perspective)",
        "text": "Jeremy, let's look at this from the spiritual side. Biblical love is patient and kind, but it never promotes irresponsibility. Proverbs warns us repeatedly about putting up security for a neighbor's debt. If we carry Caleb's thousand-dollar light bill while he works unlicensed under the table, we are robbing him of the trial he needs to grow. Scripture says a man must provide for his own household. Helping is good, but when it crosses into enabling, it is no longer love."
    },
    {
        "agent": "Maxx (Secular & Pragmatic)",
        "text": "Hold on, Arelius. Let's get down to the raw numbers. The secular view is cold but true: credit is your economic lifeline. A unpaid thousand-dollar utility bill under Anthony's name ruins his ability to lease a place, buy tires, or get loans when he needs them. Caleb is unlicensed. Bouncing between gig jobs is unstable. If he can't get licensed, he shouldn't run a household of six on hope. Anthony has to shut the bill off to protect his own survival. It is just math."
    },
    {
        "agent": "Orion (Biased & Family-First)",
        "text": "You guys are talking like machines. Look at the actual home. We are talking about four young kids in a wild, chaotic house. If Anthony cuts the power, those kids sit in the dark. Caleb is working HVAC, grinding in hot attics, trying to make things work. How do you just walk away? Family doesn't calculate credit scores when children are involved. You absorb the financial blow because you love them. You just deal with it."
    },
    {
        "agent": "Dr. Jeremy Brown (Direct, Friend)",
        "text": "Orion, that emotional bias feels right, but it's a trap. Medical and psychological data shows that chronic stress from carrying others' burdens breaks down the helper. If Anthony collapses from high blood pressure, stress, and smoking, who helps the kids then? You cannot pour from an empty cup. Real compassion requires setting a hard boundary so they are forced to find local assistance programs."
    },
    {
        "agent": "Jarvis (System Architecture & Structures)",
        "text": "And structurally, the Verizon bill pattern shows this is a recurring loop. You switch companies or names to bypass the system, but the debt remains. The only way to break this is to face the collections, clear Anthony's name, and transfer the active utilities to Caleb, forcing them to establish a payment plan directly with the utility company."
    },
    {
        "agent": "Xoras (Executive Summary)",
        "text": "Jeremy, you are standing there listening to this debate. The lesson is balance. The biased view wants to shield them from pain, the secular view wants to cut them off to protect the assets, and the biblical view demands truth, responsibility, and stewardship. The path of wisdom is to help them transition to their own name, stop carrying their weight, and protect your own health. Swarm discussion complete."
    }
]

def run_debate():
    print("==========================================================")
    print("      XORAS SYSTEMS: TRIPLE PERSPECTIVE DEBATE")
    print("==========================================================\n")
    
    for segment in PERSPECTIVE_DEBATE:
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
