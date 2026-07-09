# --- XORAS SYSTEMS: UNBIASED OBJECTIVE PERSPECTIVE ---
# File: Source/objective_view.py
# Classification: [PRODUCTION // RESEARCH SWARM]

import sys
import time
import subprocess

UNBIASED_SPEECH = (
    "Anthony, looking at this completely objectively, stripped of emotion, the facts are simple. "
    "You do not live in that home, but you hold one hundred percent of the financial and legal liability for it. "
    "The bill is over one thousand dollars and is growing. The current residents cannot afford their utility consumption "
    "and are not paying it. Leaving your name on the account does not solve their problem; it only delays the crash while "
    "destroying your own financial stability and spiking your stress. Mechanically, the only logical move is to shut down "
    "the account. This stops your financial leakage immediately and forces them to transition to their own name, negotiate a "
    "payment plan, or apply for state utility assistance. It is the only outcome where both parties are forced to live in reality."
)

def execute_speech():
    print("==========================================================")
    print("[Xoras (Sovereign Core - Unbiased Audit)]")
    print(f"Speaking: \"{UNBIASED_SPEECH}\"\n")
    sys.stdout.flush()
    
    # Call macOS 'say' command
    subprocess.run(["say", UNBIASED_SPEECH])
    
    print("==========================================================")
    print("                 OBJECTIVE AUDIT COMPLETED")
    print("==========================================================")

if __name__ == '__main__':
    execute_speech()
