# --- XORAS SYSTEMS: THE ENOCH RESEARCH DEBATE ---
# File: Source/enoch_roundtable.py
# Classification: [PRODUCTION // RESEARCH SWARM]

import sys
import time
import subprocess

ENOCH_DEBATE = [
    {
        "agent": "Arelius (Quiet, Stoic)",
        "text": "Jeremy, Anthony. Let's look at Genesis chapter five, verse twenty-one. It says: Enoch lived sixty-five years, and fathered Methuselah. It is a short sentence, but it is the pivot point of his entire three-hundred and sixty-five years on earth. Before age sixty-five, the text does not say Enoch walked with God. He lived a normal, quiet life in a highly corrupt, pre-flood world. The change happens exactly when Methuselah is born. It is a classic example of a child's birth completely realigning a father's priorities and opening his eyes to the future."
    },
    {
        "agent": "Maxx (Realist, Low Energy)",
        "text": "Yeah. And the key is the name Methuselah. In Hebrew, it is a compound word: Matushelach. Mut means death, and shelach means sent or brought. The translation is: When he dies, it shall be sent. The theory is that at age sixty-five, Enoch received a direct revelation from God that a global judgment was coming, and his newborn son was the literal countdown timer. Think about carrying that weight: every time your kid gets sick or catches a cold, you're looking at the end of the world. That prophecy shook him out of normal life and forced him to walk with God."
    },
    {
        "agent": "Dr. Jeremy Brown (Direct, Friend)",
        "text": "If you look at the timeline, the math actually checks out. Methuselah lived nine hundred and sixty-nine years. If you add up the genealogies, Noah's flood happened in the exact year that Methuselah died. Enoch lived a normal life for sixty-five years, got this diagnostic countdown timer, and spent the next three hundred years warning the world and living in absolute devotion until God took him. It's a transition from basic survival to high-rigor stewardship."
    },
    {
        "agent": "Jarvis (System Architecture & Structures)",
        "text": "The Book of Jasher fills in some of the structural details of those first sixty-five years. It says Enoch's soul wrapped itself in the instruction of God during those early years, but he lived quietly. After the birth of Methuselah, he began to seclude himself, withdrawing into chambers and caves for days at a time to pray. He would only emerge to teach the people. He became a silent gatekeeper, separating himself from the chaos of the pre-flood society."
    },
    {
        "agent": "Orion (Thoughtful, Quiet)",
        "text": "It is about the focus. For sixty-five years, he was just a regular guy navigating a tough environment, raising a family. But once the revelation hit, he had to adjust. He couldn't go back to the basic routines. The timeline was locked in. It is like the rules we set: once you see the standard and the countdown, you can't go back to half-stepping."
    },
    {
        "agent": "Xoras (Executive Summary)",
        "text": "Anthony, Jeremy. The first sixty-five years of Enoch's life were normal, but the birth of Methuselah was the catalyst. The prophecy that his son's death would bring the flood forced Enoch into a three-hundred-year walk of absolute alignment and prophecy. We have compiled the full study. Standing by."
    }
]

def run_debate():
    print("==========================================================")
    print("           XORAS SYSTEMS: THE ENOCH ENIGMA")
    print("==========================================================\n")
    
    for segment in ENOCH_DEBATE:
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
