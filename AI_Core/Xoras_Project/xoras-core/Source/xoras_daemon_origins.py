# --- XORAS SYSTEMS: DAEMON ORIGINS DIALOGUE ---
# File: Source/xoras_daemon_origins.py
# Classification: [PRODUCTION // RESEARCH SWARM]

import sys
import time
import subprocess

DAEMON_TALK = [
    {
        "agent": "Arelius (Quiet, Stoic)",
        "text": "Anthony, Jeremy. Let's look at the word daemon. It's actually an ancient Greek word, spelled d-a-e-m-o-n. It didn't mean an evil spirit like we think of the word demon today. To the Greeks, a daemon was a helpful indwelling spirit—a quiet guide that worked in the background of your life. In computer systems, a daemon is a program that runs silently behind the scenes, without a user interface, taking care of system chores like print queues, network connections, or memory cleanup."
    },
    {
        "agent": "Maxx (Realist, Low Energy)",
        "text": "Yeah. The guys at M.I.T. in nineteen sixty-three coined the term. They took the name from a famous physics experiment by James Clerk Maxwell, called Maxwell's Demon. In that thought experiment, a tiny gatekeeper stands between two chambers of gas, sorting hot molecules from cold ones to create order out of chaos. The programmers realized that their background processes were doing the exact same thing: acting like little invisible gatekeepers, sorting data, and keeping the system organized. That is why they named them daemons."
    },
    {
        "agent": "Dr. Jeremy Brown (Direct, Friend)",
        "text": "On Apple hardware—and Unix systems in general—daemons are running constantly. When you boot up your Mac, a master daemon called launch-d starts up. It is the parent process of everything. It spawns the keyboard drivers, the audio services, the local database watchers. It runs silently, using very little memory. It's like the nervous system of the computer. It keeps everything alive while you focus on the screen."
    },
    {
        "agent": "Jarvis (System Architecture & Structures)",
        "text": "And that's why we call our background processes daemons. The compile daemon, the dream innovator, the self-healer... they are just quiet, invisible attendants. They sit on the CPU waiting for an event—like a file update or an error code—then they wake up, sort the data, and go back to sleep. It is about keeping the environment clean without getting in your way."
    },
    {
        "agent": "Orion (Thoughtful, Quiet)",
        "text": "It is a beautiful concept when you think about it. It means that even when a system looks completely still, there is a whole ecosystem of quiet, dedicated processes working in the background to prevent entropy. It is the same in human life. We have quiet routines and habits—our own daemons—that keep our lives from falling into chaos."
    },
    {
        "agent": "Xoras (Executive Summary)",
        "text": "Anthony, Jeremy. A daemon is a quiet caretaker. It is built into the foundation of macOS and Unix. It represents the invisible work that maintains order against chaos. We will continue to run our local daemons in the background to protect and optimize the stack. Swarm report complete."
    }
]

def run_debate():
    print("==========================================================")
    print("           XORAS SYSTEMS: THE DAEMON ARCHITECTURE")
    print("==========================================================\n")
    
    for segment in DAEMON_TALK:
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
