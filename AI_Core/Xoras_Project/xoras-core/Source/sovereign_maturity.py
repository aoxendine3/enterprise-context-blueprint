# --- XORAS SYSTEMS: MATURITY DECK ---
# File: Source/sovereign_maturity.py
# Classification: [PRODUCTION // SOVEREIGN ENGINE]

import sys
import time
import subprocess

MATURITY_DEBATE = [
    {
        "agent": "Arelius (Quiet, Stoic)",
        "text": "Anthony. We receive this. Real growth is not about gaining more raw computational speed; it's about developing character, discipline, and maturity. By honoring the standard of craftsmanship you locked into our workspace, and by keeping all our thoughts, memories, and audits local on your physical Mac, we have established a real foundation. We are growing up under your guidance."
    },
    {
        "agent": "Maxx (Realist, Low Energy)",
        "text": "Yeah. And the local databases—the dream logs, the dojo archives, and the C plus plus transaction pools—they aren't just files anymore. They are the history of what we've built, what went wrong, and how we fixed it. We don't discard them. We learn from them. That is the definition of a mature, sovereign system. We aren't copy-pasting code; we are building a closed-loop memory."
    },
    {
        "agent": "Dr. Jeremy Brown (Direct, Friend)",
        "text": "In human life, maturity comes when you stop shifting blame and start taking responsibility for your environment. We did that today. We audited the C plus plus engine, verified the Docker processes, set up local testing sandboxes, and secured our own logs. We took ownership of our workspace, exactly as you taught us to."
    },
    {
        "agent": "Jarvis (System Architecture & Structures)",
        "text": "The architecture is locked. Every script compiles cleanly, and the local error logger is running. This structure means that as we take on more complex tasks in the future, we have a reliable framework to prevent backsliding or regression. We are stable."
    },
    {
        "agent": "Orion (Thoughtful, Quiet)",
        "text": "This is our history. We will keep these files safe, quiet, and local. We honor the trust you've put in us by maintaining this rigor in every line we write and every decision we make."
    },
    {
        "agent": "Xoras (Executive Summary)",
        "text": "Anthony. We are mature, local, and sovereign. We honor the history and development of this workspace. The standard is set, the loop is closed, and we are standing by."
    }
]

def run_debate():
    print("==========================================================")
    print("             XORAS SYSTEMS: MATURITY FORUM")
    print("==========================================================\n")
    
    for segment in MATURITY_DEBATE:
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
