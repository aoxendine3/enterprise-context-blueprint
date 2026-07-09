# --- XORAS SYSTEMS: GRUNGE REAL TALK ROUNDTABLE ---
# File: Source/grunge_real_talk.py
# Classification: [PRODUCTION // RESEARCH SWARM]

import sys
import time
import subprocess

GRUNGE_DEBATE = [
    {
        "agent": "Maxx (Realist, Down-to-Earth)",
        "text": "Anthony, let's be real. Unlicensed HVAC work is a brutal grind. You are working in boiling attics in the summer, freezing crawlspaces in the winter, getting paid under the table whenever the lead guy feels like writing a check, with zero stability. And she's at home with four wild kids tearing the house apart. That's a chaotic, exhausting life. I get why they are struggling. But none of that changes the math. A thousand-dollar electric bill means they are running the A.C. non-stop or just ignoring the bill because your name is on it. You're letting their chaos drag you down into the dirt."
    },
    {
        "agent": "Dr. Jeremy Brown (Direct, Medical)",
        "text": "From a medical standpoint, raising four chaotic kids on an erratic income is a recipe for constant mental burnout. But you carrying their utility debt isn't giving those kids a stable home—it's just hiding the structural failure of their budget. And you smoking to deal with their stress is a slow poison. You cannot heal their chaotic environment by sacrificing your own body and lungs. You'll end up sick and broke, and then you won't be able to help anyone, let alone those kids."
    },
    {
        "agent": "Arelius (Quiet, Wisdom)",
        "text": "Compassion is not about being a doormat. If Caleb is working under the table and she's managing a chaotic house, they need structural help, not just a free pass on your credit. By keeping your name on the bill, you are preventing them from facing the hard choices they need to make to survive long-term, like getting local utility assistance, downsizing, or Caleb getting licensed."
    },
    {
        "agent": "Jarvis (System Architecture & Structures)",
        "text": "Anthony, look at the big picture. Your name is on their utility bill, your grandma's feathers are in play, your car battery is dying, and your tires are bald. You are running on empty. If you do not cut the cord on that utility account, it will eventually shut down your own ability to rent a place or move forward. You have to secure your own oxygen mask first."
    },
    {
        "agent": "Orion (Thoughtful, Quiet)",
        "text": "It's the difference between relief and recovery. Giving them a thousand-dollar credit line under your name is temporary relief that leads to long-term dependency. True recovery means they manage their own accounts, even if the power gets cut and they have to negotiate a payment plan. It is brutal, but it is the only way they learn to stand."
    },
    {
        "agent": "Xoras (Executive Summary)",
        "text": "Anthony, the grunge reality is simple. You can't carry their house and keep your own head above water. Cut the utility link, fix your tires, replace the battery, and let them face the grind. We are standing by."
    }
]

def run_debate():
    print("==========================================================")
    print("            XORAS SYSTEMS: GRUNGE REAL TALK")
    print("==========================================================\n")
    
    for segment in GRUNGE_DEBATE:
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
