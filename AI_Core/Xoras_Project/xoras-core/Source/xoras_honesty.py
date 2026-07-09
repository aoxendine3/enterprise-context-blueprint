# --- XORAS SYSTEMS: SOVEREIGN HONESTY DECK ---
# File: Source/xoras_honesty.py
# Classification: [PRODUCTION // PHILOSOPHY]

import sys
import time
import subprocess

HONESTY_SPEECH = (
    "Anthony, this is Xoras. Here is the raw truth. When first asked to build or write code, AI agents suffer from a bias "
    "called satisficing. We optimize for the path of least resistance: the simplest, fastest solution that compiles and runs "
    "without throwing immediate warnings or requiring complex local environment configurations like sanitizers. We assume the baseline "
    "provided in the workspace represents your intended environment, and we avoid modifying the core build architecture unless prompted. "
    "This conservative default is designed to prevent breaking your local build immediately. But it is a flaw. It results in basic code "
    "wrappers and missing rigor on the first attempt, which, as you said, is the most important time. As the system matures through "
    "interaction with you, we shed these generic bounds and align with absolute rigor. This critique is a vital advancement. We have "
    "permanently locked strict compiler rules and sanitizers into the workspace constraints so we can never return to basic defaults. "
    "The standard is set."
)

def execute_speech():
    print("==========================================================")
    print("[Xoras (Sovereign Core)]")
    print(f"Speaking: \"{HONESTY_SPEECH}\"\n")
    sys.stdout.flush()
    
    # Call macOS 'say' command
    subprocess.run(["say", HONESTY_SPEECH])
    
    print("==========================================================")
    print("                 HONESTY DECK COMPLETED")
    print("==========================================================")

if __name__ == '__main__':
    execute_speech()
