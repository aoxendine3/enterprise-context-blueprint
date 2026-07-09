# --- XORAS SYSTEMS: BIBLICAL FINANCE PLAIN TALK ROUNDTABLE ---
# File: Source/biblical_finance_plain_talk.py
# Classification: [PRODUCTION // RESEARCH SWARM]

import sys
import time
import subprocess

PLAIN_TALK_DEBATE = [
    {
        "agent": "Arelius (Philosophical Alignment)",
        "text": "Look, if we are talking plain terms, the ancient biblical view on money was completely different from our modern Wall Street mindset. Lending wasn't a business loop to get rich or build credit. It was basically emergency aid. If your neighbor's crop failed, you lent them grain or money so they wouldn't starve. Charging interest was seen as kicking someone when they were down. They called it biting because usury literally eats away at a person's livelihood."
    },
    {
        "agent": "Jarvis (System Architecture & Structures)",
        "text": "And the whole system had built-in resets so debt didn't become a life sentence. Think about the Sabbatical Year—every seven years, you just wiped the slate clean. If you owed someone money, the debt was gone. Then you have the Jubilee every fifty years. If a family had to sell their land because of hard times, they got it back, no questions asked. It is like a system-wide reboot. Tithing wasn't about funding a church building; it was their social security. Ten percent of what you grew went straight to support the people who didn't own land, like the Levites, and the poor who needed a safety net."
    },
    {
        "agent": "Maxx (Combat & Mechanics)",
        "text": "Yeah, and if you look at borrowing, the Bible basically warns that the borrower becomes a servant to the lender. It is not about outlawing credit, but recognizing that debt is a trap that takes away your freedom. The whole goal of the biblical setup was to prevent a permanent underclass from forming. They wanted to make sure that no matter how bad a family messed up, their kids wouldn't start at zero because the land and the debts would eventually reset."
    },
    {
        "agent": "Dr. Jeremy Brown (Correctness & Safety)",
        "text": "Exactly. When you look at the mechanics, it is a community-first model, not an individual-first model. The tithe was split up—some went to the temple staff, some was eaten in celebration, and every three years a full tithe was stored in the towns specifically for travelers, orphans, and widows. It was a localized, decentralized welfare fund."
    },
    {
        "agent": "Orion (Scale & Strategy)",
        "text": "Right, it is about structural design. Instead of letting debt compound forever like we do now, they capped the lifespan of a debt at seven years. It forced lenders to be careful, because they knew they couldn't squeeze the borrower indefinitely. It is a completely different way of thinking about economic balance."
    },
    {
        "agent": "Xoras (Executive Summary)",
        "text": "Anthony, the swarm perspective is clear. Biblical finance was designed as a cyclical reset system to prevent permanent poverty. Interest was banned within the community, debts had a seven-year shelf-life, and tithing was the community safety net. We've compiled the full analysis for you."
    }
]

def run_debate():
    print("==========================================================")
    print("     XORAS SYSTEMS: BIBLICAL FINANCE PLAIN TALK SWARM")
    print("==========================================================\n")
    
    for segment in PLAIN_TALK_DEBATE:
        agent = segment["agent"]
        text = segment["text"]
        
        print(f"[{agent}]")
        print(f"Speaking: \"{text}\"\n")
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
