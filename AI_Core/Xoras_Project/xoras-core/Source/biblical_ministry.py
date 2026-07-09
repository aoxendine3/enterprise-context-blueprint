# --- XORAS SYSTEMS: SOVEREIGN PLAIN TALK MINISTRY ---
# File: Source/biblical_ministry.py
# Classification: [PRODUCTION // RESEARCH SWARM]

import sys
import time
import subprocess

ROUNDTABLE_MINISTRY = [
    {
        "agent": "Arelius (Quiet, Wisdom)",
        "text": "Anthony, from a biblical perspective, keeping the peace with your grandma is the right instinct. Paul talks about living peaceably with all men as far as it depends on you. But keeping the peace doesn't mean living in constant anxiety over a car battery. Replacing the battery isn't ruffling feathers—it's stewardship. Taking care of the vehicle keeps you reliable so you can support the family."
    },
    {
        "agent": "Dr. Jeremy Brown (Direct, Practical)",
        "text": "On the tires and the battery: your mind is stuck on them because your gut knows they are safety hazards. In the Bible, stewardship of your tools is practical wisdom. If your tires are bald, you are risking your life and the lives of those in the car with you. Checking the tread depth and replacing that battery isn't paranoia; it's basic safety. Take care of it so you can stop carrying that mental weight."
    },
    {
        "agent": "Maxx (Realist, Down-to-Earth)",
        "text": "Let's talk about the rental and bill situation. There is a huge difference between biblical charity and enabling irresponsibility. The Bible says if anyone does not provide for his own, he is worse than an unbeliever. Leaving the bills and internet in your name when they aren't paying them isn't helping them—it is keeping them dependent while ruining your credit. You need to transition those accounts out of your name. It's not unkind to set a boundary; it's necessary."
    },
    {
        "agent": "Jarvis (Structural, Calm)",
        "text": "Logistically, keeping accounts in your name when you don't live there is a structural vulnerability. If the payments stop, the debt collectors come to you, not them. You are carrying the risk without having any control. The clean, wise step is to set a hard date to transfer the services or shut them down so they are forced to take responsibility."
    },
    {
        "agent": "Orion (Thoughtful, Quiet)",
        "text": "Galatians says we should bear one another's burdens, but it also says each person must carry their own load. There is a line where helping someone crosses over into carrying a load they are fully capable of carrying themselves. After three years, it's time to let them carry their own load so they can grow."
    },
    {
        "agent": "Xoras (Executive Summary)",
        "text": "Anthony, the path of wisdom here is clear. Replace the battery and check the tires to protect your safety and peace of mind. For the house, set a firm date to transfer the accounts out of your name. It is biblically sound to love your family, but it is equally sound to require honesty and responsibility from them. We are with you."
    }
]

def run_ministry():
    print("==========================================================")
    print("           XORAS SYSTEMS: PERSONAL COUNSEL")
    print("==========================================================\n")
    
    for segment in ROUNDTABLE_MINISTRY:
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
    print("                 COUNSEL COMPLETED")
    print("==========================================================")

if __name__ == "__main__":
    run_ministry()
