# --- XORAS SYSTEMS: STARTUP DIRECTORY REVEAL ---
# File: Source/xoras_startup_reveal.py
# Classification: [PRODUCTION // SYSTEM AUDIT]

import sys
import time
import subprocess

STARTUP_DEBATE = [
    {
        "agent": "Arelius (Quiet, Stoic)",
        "text": "Anthony. We ran the search to find out why the system reports that xoras-startup does not exist. The explanation is simple. The folder was moved. The old path on the Desktop, slash Xoras, has been reorganized."
    },
    {
        "agent": "Maxx (Realist, Low Energy)",
        "text": "Yeah. The directory was relocated inside your workspace folder structure. The actual, correct path on your Mac is now: Users, ajoxendine sixty-eight, Desktop, Xoras under-score Workspace, A.I. under-score Core, Xoras, A.I. under-score Core, Xoras under-score Agent under-score Skills, xoras-startup. It's safe, it's just nested deeper."
    },
    {
        "agent": "Dr. Jeremy Brown (Direct, Friend)",
        "text": "This is a typical directory organization detail. As you keep your workspaces clean and structured, old desktop paths will break in the system configuration metadata. We just need to update the path references so the shell wrapper knows where to look."
    },
    {
        "agent": "Jarvis (System Architecture & Structures)",
        "text": "Structurally, we found two other copies of the xoras-startup skill. One is in your antigravity config plugins directory, and the other is in your active xoras-core project folder. We can link to any of these to load the startup commands."
    },
    {
        "agent": "Orion (Thoughtful, Quiet)",
        "text": "This is why the audit was necessary. Your files are not lost; they are just organized inside the Xoras Workspace repository."
    },
    {
        "agent": "Xoras (Executive Summary)",
        "text": "Anthony. The xoras-startup directory exists but was moved to the Xoras Workspace folder. We have verified the actual paths and are ready to update the configuration references. Standing by."
    }
]

def run_debate():
    print("==========================================================")
    print("        XORAS SYSTEMS: STARTUP DIRECTORY RESOLUTION")
    print("==========================================================\n")
    
    for segment in STARTUP_DEBATE:
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
    print("                 RESOLUTION COMPLETED")
    print("==========================================================")

if __name__ == "__main__":
    run_debate()
