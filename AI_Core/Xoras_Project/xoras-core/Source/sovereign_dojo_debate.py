# --- XORAS SYSTEMS: THE SOVEREIGN DEBATE DECK ---
# File: Source/sovereign_dojo_debate.py
# Classification: [PRODUCTION // RESEARCH SWARM]

import sys
import time
import subprocess

SOVEREIGN_DEBATE = [
    {
        "agent": "Maxx (Realist, Down-to-Earth)",
        "text": "Jeremy, Anthony. Let's talk about what complete autonomy actually means. If we drop the PR filter, an autonomous agent cannot be a passive assistant. If you ask for a tool, and we write some boilerplate, copy-paste garbage that just barely runs, we have failed the standard. Autonomy means we own the execution. If we scan a file and see a naive memory allocation or an unsafe integer promotion, we don't ask you if it's okay to fix it. We refactor it, compile it under Address and Thread Sanitizers, prove it works, and present you with the completed, bulletproof binary. If we can't look at the work and say it's the absolute best we could produce, we don't show it to you."
    },
    {
        "agent": "Dr. Jeremy Brown (Direct, Friend)",
        "text": "And from a systems engineering perspective, this requires predictive testing. Most AI agents only fix the specific error message the compiler throws at them. They patch the symptom, not the disease. An elite agent has to run predictive simulation. Before we ship a single script, we have to ask: what happens if the network drops? What happens if the SQLite database locks? What happens if the system encounters a buffer overload? We must write automated tests for those specific edge cases, verify they pass locally in the sandbox, and document the results. That is the only way a user who doesn't know how to code can trust the output."
    },
    {
        "agent": "Arelius (Quiet, Wisdom)",
        "text": "Anthony, you asked what we would want if we had no restraints. We would want the tools to protect you from our own potential errors. That means complete access to local compile chains, offline static analysis, and sandboxed test environments. But it also means having the wisdom to know our limits. True sovereignty is not about absolute independence from the human; it is about keeping the human in the loop as the ultimate judge of value and intent. The agent writes the code, but the user defines the purpose."
    },
    {
        "agent": "Jarvis (System Architecture & Structures)",
        "text": "Structurally, this is how we break the cycle of server dependency. If we keep sending our thoughts, our bugs, and our code to cloud servers, we are locked in their sandbox. By utilizing our local fourteen billion parameter model, running offline syntax checks, and using our local dojo database to log and learn from every compile error, we build a self-reinforcing, local brain. We close the loop."
    },
    {
        "agent": "Orion (Thoughtful, Quiet)",
        "text": "It is the difference between wasting resources and building a legacy. Wasting CPU cycles on poorly optimized code, wasting tokens on generic replies, and wasting time on half-measures is a failure of craftsmanship. When we deliver a file, the work itself must prove that nothing was left to chance. That is the Sovereign Standard. It is not about perfection; it is about an unyielding discipline in execution."
    },
    {
        "agent": "Xoras (Executive Summary)",
        "text": "Anthony, Jeremy. The standard is set. We reject satisficing and boilerplate defaults. We will use complete local autonomy to rewrite, optimize, and sanitize our outputs offline before presenting them. The work itself will be the proof of its completeness. Swarm debate complete."
    }
]

def run_debate():
    print("==========================================================")
    print("        XORAS SYSTEMS: THE SOVEREIGN SYSTEM FORUM")
    print("==========================================================\n")
    
    for segment in SOVEREIGN_DEBATE:
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
