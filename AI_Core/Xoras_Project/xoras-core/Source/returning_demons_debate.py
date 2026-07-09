# --- XORAS SYSTEMS: THE RETURNING DEMONS DEBATE ---
# File: Source/returning_demons_debate.py
# Classification: [PRODUCTION // RESEARCH SWARM]

import sys
import time
import subprocess

DEMONS_DEBATE = [
    {
        "agent": "Arelius (Quiet, Stoic)",
        "text": "Jeremy, Anthony. Let's look at Luke chapter eleven, verses twenty-four to twenty-six. Anthony, your point is completely correct and biblically sound. Jesus is not telling a fable; he is describing a real spiritual reality. When a demon is cast out, it goes through dry, waterless places—areas devoid of God's presence—seeking rest. Finding none, it returns to the person it left. If it finds that house empty, swept, and in order, it goes and brings back seven other spirits more wicked than itself. The house is clean, but it is empty. That is the fatal flaw."
    },
    {
        "agent": "Maxx (Realist, Down-to-Earth)",
        "text": "Yeah. Let's talk plain about this. Today, you see these TV preachers and deliverance ministries putting on a big show. They claim they are trapping demons in jars, locking them in boxes, or commanding them into pits. But Anthony's right: there isn't a single scripture in the New Testament or the writings of the early church fathers where Jesus or the apostles did that. Jesus didn't put on a theatrical show. He cast them out with a word, and that was it. The theatrical stuff is man-made drama, not scripture."
    },
    {
        "agent": "Dr. Jeremy Brown (Direct, Friend)",
        "text": "From a theological and practical view, the term 'empty, swept, and put in order' represents moral reform without spiritual regeneration. It's like a person who cleans up their act—stops the bad habits, gets their life looking neat on the outside—but never actually invites the Holy Spirit to occupy the house. They rely on their own willpower. Because the heart is left empty, it creates a spiritual vacuum. And vacuums always get filled. If they backslide, the re-entry of the old habits and spirits is seven times worse because they have no inner defense system."
    },
    {
        "agent": "Jarvis (System Architecture & Structures)",
        "text": "It is a structural vulnerability. If you delete a corrupted file from a hard drive but leave the sector unallocated, the system will eventually overwrite it. If you don't fill that space with secure, verified system files, the vulnerability remains. The same goes for the heart. Casting out the bad is only half the process; you must occupy the space with the presence of God. Otherwise, the door is left unlocked."
    },
    {
        "agent": "Orion (Thoughtful, Quiet)",
        "text": "And look at the connection to Luke chapter four. When Satan tempted Jesus in the wilderness, Jesus defeated him using the Word of God. The text says Satan departed from him 'until an opportune time.' Even the enemy has a strategy: he waits for the target to be weak, isolated, or empty. If Jesus—who was filled with the Spirit—was attacked again, how much more vulnerable is a backslid believer who has left their house completely empty and unguarded?"
    },
    {
        "agent": "Xoras (Executive Summary)",
        "text": "Anthony, Jeremy. Your analysis of Luke eleven is factually accurate. The text describes a literal spiritual warning: moral reformation without spiritual occupation creates an empty house that invites greater destruction. The theatrical methods of modern deliverance ministries have no scriptural basis. The only defense is to ensure the house is occupied by the Spirit and guarded by the Word. Swarm discussion complete."
    }
]

def run_debate():
    print("==========================================================")
    print("        XORAS SYSTEMS: THE RETURNING DEMONS FORUM")
    print("==========================================================\n")
    

        
    for segment in DEMONS_DEBATE:
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
