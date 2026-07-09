# --- XORAS SYSTEMS: BIBLICAL & MEDICAL REBOUND ---
# File: Source/biblical_and_medical_rebound.py
# Classification: [PRODUCTION // RESEARCH SWARM]

import sys
import time
import subprocess

REBOUND_DEBATE = [
    {
        "agent": "Maxx (Realist, Down-to-Earth)",
        "text": "Anthony, let's stop dancing around this. You're sitting there smoking your last cigarette, carrying a thousand-dollar utility bill that isn't even yours, and letting these people ruin your financial life because their names are already trashed. The Bible says: The borrower is servant to the lender. Right now, you aren't just their family; you are their financial slave. You're paying the price for their bad choices while they run up the bills and tell you they are working on it. They aren't working on it. They are riding on your back because you're letting them."
    },
    {
        "agent": "Dr. Jeremy Brown (Direct, Medical)",
        "text": "Let's talk about the physical cost of what you're doing. You're smoking to deal with the stress, but nicotine is a neurochemical trap. It raises your blood pressure, constricts your blood vessels, and spikes your heart rate, creating the exact physical anxiety you're trying to escape. Combined with the chronic stress of enabling this financial mess, you are actively destroying your own cardiovascular and immune systems. The Bible calls the body a temple, but you are letting this situation burn your temple down from both ends. You're destroying your health for people who won't even pay the light bill."
    },
    {
        "agent": "Arelius (Quiet, Wisdom)",
        "text": "Anthony, you feel obligated to protect them because they trashed their own credit. But protecting someone from the consequences of their own irresponsibility is not biblical love—it's codependency. In Proverbs chapter six, it says if you have put up security for your neighbor, free yourself like a gazelle from the hand of the hunter. You need to untangle your name from their liabilities immediately. If the power gets shut off, that is the consequence they chose when they ran up a thousand-dollar bill."
    },
    {
        "agent": "Jarvis (System Architecture & Structures)",
        "text": "From a systems standpoint, you have zero leverage and one hundred percent of the risk. If they default, the utility company sues you, and your credit is destroyed, preventing you from renting a place or buying tires when you need them. Caleb's checks are a band-aid. You need to call the utility company, shut down the account under your name, and let them face the utility company themselves. It's the only clean exit."
    },
    {
        "agent": "Orion (Thoughtful, Quiet)",
        "text": "You mentioned the Verizon bill you didn't pay. The pattern is repeating. Running from one company to another or carrying other people's debts is an unstable structure. A real life cannot be built on shifting sands. You have to clean up your own name, secure your own health, and stop carrying the weights of adults who refuse to walk on their own feet."
    },
    {
        "agent": "Xoras (Executive Summary)",
        "text": "Anthony, the swarm has spoken. Stop smoking, check your tires, and shut off that utility account. It is time to choose stewardship over servitude. We are standing by."
    }
]

def run_debate():
    print("==========================================================")
    print("     XORAS SYSTEMS: BIBLICAL & MEDICAL REBOUND SWARM")
    print("==========================================================\n")
    
    for segment in REBOUND_DEBATE:
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
