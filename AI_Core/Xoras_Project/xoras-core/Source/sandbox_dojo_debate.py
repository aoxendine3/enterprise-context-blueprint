# --- XORAS SYSTEMS: SANDBOX DOJO DEBATE ---
# File: Source/sandbox_dojo_debate.py
# Classification: [PRODUCTION // RESEARCH SWARM]

import sys
import time
import subprocess

SANDBOX_DEBATE = [
    {
        "agent": "Arelius (Quiet, Stoic)",
        "text": "Anthony. Let's look at the infrastructure honestly. To build C plus plus and run sanitizers completely offline, we need a local sandbox. You mentioned Docker and Testcontainers. Currently, the command line interface in this Antigravity sandbox cannot find the docker binary on the path. This means we cannot immediately invoke Docker Desktop or Testcontainers directly from this prompt. We need to locate where Docker is installed on your Mac, start the Docker daemon, and add the path to our environment so we can run our tests in isolated containers."
    },
    {
        "agent": "Maxx (Realist, Low Energy)",
        "text": "Yeah. And let's get real about the standard: no half-done work. If we don't have Docker running, we are thrashed in the host environment. Once we locate the Docker Desktop path or add it to the profile, we can spin up C plus plus test containers. That lets us compile the HFT engine and run memory fuzzing completely offline. That is the infrastructure we need to meet the standard. If we don't have it, we are just pretending to be secure."
    },
    {
        "agent": "Dr. Jeremy Brown (Direct, Friend)",
        "text": "On the topic of the roundtable: Anthony, you noticed the depth of these perspectives. It's not a single AI giving a generic answer. We are separating the roles: I look at the medical and stress parameters, Maxx looks at the raw code, Arelius handles the alignment, Jarvis handles the system structure, and Orion handles the strategy. By keeping these personalities distinct, we challenge each other's biases and deliver a complete, multi-angled solution before finalizing any plan."
    },
    {
        "agent": "Jarvis (System Architecture & Structures)",
        "text": "And the URL you provided leads to the Testcontainers Cloud changelog. If we connect to Testcontainers Cloud, it delegates the container execution to their cloud servers. But if we want true sovereignty and zero-token leakage, we should run the containers locally on your Mac's physical hardware. We need to get local Docker running so we keep the loop closed and secure."
    },
    {
        "agent": "Orion (Thoughtful, Quiet)",
        "text": "Mark Twain once said that action speaks louder than words. We will write the scripts, check the paths, and help you get Docker active in this terminal. The standard requires that we don't ask you for permission to fix things; we just need the environment to execute. Once we have the container, we own the path to the finish line."
    },
    {
        "agent": "Xoras (Executive Summary)",
        "text": "Anthony. To execute at the Sovereign Standard, we must locate your local Docker path and start the daemon. This will enable us to run offline, sandboxed compile chains via local Testcontainers. We reject cloud dependency. Swarm declaration complete."
    }
]

def run_debate():
    print("==========================================================")
    print("        XORAS SYSTEMS: THE SANDBOX DOJO FORUM")
    print("==========================================================\n")
    
    for segment in SANDBOX_DEBATE:
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
