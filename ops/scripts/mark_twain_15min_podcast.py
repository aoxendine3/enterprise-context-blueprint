#!/usr/bin/env python3
"""
=============================================================================
XORAS SOVEREIGN PODCAST: TOP MARK TWAIN READS & LITERARY MASTERPIECES (15 MIN)
Spoken Engine: Kokoro v1.0 ONNX Neural Voice System via sync_stage_engine_kokoro
Stage Sync: http://127.0.0.1:8080/customer_app.html / current_timing.json
=============================================================================
"""

import os, sys, time, socket, subprocess, webbrowser
from concurrent.futures import ThreadPoolExecutor

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FULLSCREEN_UI_DIR = os.path.join(SCRIPT_DIR, "fullscreen_ui")
if FULLSCREEN_UI_DIR not in sys.path:
    sys.path.insert(0, FULLSCREEN_UI_DIR)

from sync_stage_engine_kokoro import synthesize_kokoro_payload, play_and_sync_payload, get_kokoro_engine

PODCAST_TURNS = [
    (
        "orion",
        "Welcome everyone to XORAS Sovereign Broadcast. Today we are bringing you a full fifteen minute deep dive podcast into the extraordinary life, sharp wit, and immortal literary works of Samuel Langhorne Clemens, universally celebrated by his iconic pen name, Mark Twain. I am Orion, directing today's stage, and joined by our core collective. Over the next quarter hour, we will examine Twain's greatest masterpieces—from the winding currents of the Mississippi River to the feudal court of King Arthur. Maxx, start us off with Twain's early life and how the Mississippi River forged his unique voice."
    ),
    (
        "maxx",
        "Thanks Orion. To understand Mark Twain, you have to understand the Mississippi River in the eighteen forties and fifties. Born in Florida, Missouri, and raised in Hannibal, young Sam Clemens lived on the bank of America's primary artery of trade and culture. The phrase 'Mark Twain' itself comes from steamboat navigation terminology—a riverboat leadman's call signifying a water depth of two fathoms, or twelve feet, which meant safe water for the vessel. Twain was a riverboat pilot, a silver miner in Nevada, a newspaper printer, and a globetrotting correspondent. When he started writing, he brought an unprecedented authenticity to American literature. Before Twain, much of American literature tried to emulate formal European prose. Twain broke that mold entirely by using the vernacular—the living, breathing, humorous, and sometimes raw spoken language of real people. Vance, how does that vernacular shine in Twain's breakthrough works?"
    ),
    (
        "vance",
        "William Vance here. Twain's breakthrough came with his eighteen sixty five short story, The Celebrated Jumping Frog of Calaveras County. It captured the gold rush spirit of California and the Western mining camps, relying on framed narrative storytelling and West Coast American humor. But his first major full-length masterpiece came in eighteen seventy six with The Adventures of Tom Sawyer. On the surface, Tom Sawyer is a nostalgic, idyllic portrait of boyhood in nineteenth century Hannibal, disguised as the fictional town of St. Petersburg. We all remember the famous fence whitewashing scene, where Tom cunningly turns forced labor into an exclusive privilege, convincing his friends to pay him with trinkets just for the chance to slap paint on a fence. But under that playful boyhood adventure lies a biting satire of small-town hypocrisy, rigid religious piety, and social conformity. Clara, let's talk about the book that built on Tom Sawyer and became Twain's ultimate masterpiece."
    ),
    (
        "clara",
        "Clara here. That book, of course, is Adventures of Huckleberry Finn, published in eighteen eighty four. Ernest Hemingway famously declared that all modern American literature comes from one book by Mark Twain called Huckleberry Finn. What makes Huckleberry Finn a masterpiece of world literature is its courageous moral core. Huck, an uneducated outcast boy fleeing his abusive drunken father, travels down the Mississippi River on a raft alongside Jim, an enslaved man escaping bondage. Twain uses Huck's first-person perspective to expose the profound moral corruption of a society that claims to be civilized and Christian while upholding human slavery. The climax of Huck's internal conflict occurs when he believes that helping Jim escape is a sin that will condemn his soul to hell. Huck weighs the hypocritical rules of society against his genuine love and respect for Jim, and famously declares: 'All right, then, I'll go to hell.' In that single moment, Twain delivers one of the most powerful condemnations of institutional racism and moral hypocrisy ever penned. John, how did Twain blend technology and time travel in his later satirical novels?"
    ),
    (
        "john",
        "John here. In eighteen eighty nine, Mark Twain published A Connecticut Yankee in King Arthur's Court, which pioneered the modern concept of time travel in fiction. The story follows Hank Morgan, a nineteenth-century American factory superintendent from Hartford, Connecticut, who receives a blow to the head and wakes up in sixth-century England during the reign of King Arthur. Hank uses his knowledge of nineteenth-century science, electricity, industrial manufacturing, and weaponry to transform medieval society, earning the title of 'The Boss.' On one level, Twain lampoons romanticized medieval chivalry, feudal oppression, and monarchical tyranny. But on a deeper level, Twain offers a prophetic critique of modern technology and industrial warfare. The novel escalates into a dark, apocalyptic confrontation where Hank's advanced technological weapons annihilate the knightly order, showing that technological progress without moral wisdom leads to catastrophic destruction. Selene, what about Twain's exploration of identity and class in The Prince and the Pauper?"
    ),
    (
        "selene",
        "Selene here. Published in eighteen eighty one, The Prince and the Pauper is Twain's brilliant historical fiction set in Tudor England. Two young boys born on the exact same day in London—Prince Edward, son of King Henry the Eighth, and Tom Canty, an impoverished beggar boy from Offal Court—look identical. When they accidentally swap clothes, their identities are mistaken. Prince Edward is thrust into the brutal, impoverished underbelly of sixteenth-century English society, suffering hunger, lawlessness, and cruelty firsthand. Meanwhile, Tom Canty is forced to navigate the absurd luxury and rigid etiquette of the royal court. Through this identity switch, Twain demonstrates that empathy requires experiencing the lives of the less fortunate. Edward returns to the throne transformed into a merciful and just monarch who understands the real human cost of harsh laws. It's a timeless fable on equality, justice, and shared humanity."
    ),
    (
        "dr_jeremy",
        "Dr. Jeremy Brown here. Let's examine Twain's non-fiction and travelogues, which made him an international superstar long before his major novels. In eighteen sixty nine, Twain published The Innocents Abroad, recounting his travels aboard the steamship Quaker City through Europe and the Holy Land. It became Twain's best-selling book during his entire lifetime. Twain approached European high art, ancient monuments, and religious relics with unpretentious American skepticism and irreverence. He refused to pretend to be awed by venerated tourist traps, poking fun at pretentious guidebooks and tourists alike. Later, in eighteen eighty three, Twain published Life on the Mississippi, a rich blend of memoir and history documenting his training as a steamboat pilot and his return to the river twenty years later. Twain describes how learning to read every ripple, snag, and eddy on the river transformed his perception of nature from romantic beauty to technical reality."
    ),
    (
        "dr_eden",
        "Dr. Eden here. Twain was also a master essayist, public lecturer, and razor-sharp philosopher of human nature. In his later years, marked by personal tragedy including the deaths of his wife and daughters and financial bankruptcy from ill-fated business investments, Twain's writing took on a darker, more philosophical edge. Works like The Man That Corrupted Hadleyburg, What Is Man?, and his posthumously published Letters from the Earth reveal a deep skepticism about human vanity and morality, what he called 'the damned human race.' Yet, despite his pessimism, Twain's humor never lost its warmth or brilliance. His essays such as On the Decay of the Art of Lying and The War Prayer demonstrate his unwavering commitment to exposing political hypocrisy and the romanticization of war. His public speaking tours across the globe made him one of the most famous human beings alive in the late nineteenth century."
    ),
    (
        "orion",
        "Orion stepping back in. Looking at Mark Twain's total literary legacy, we see a writer who defined the American spirit. He demonstrated that literature could be profound without being ostentatious, that humor is one of humanity's most effective weapons against injustice, and that the true measure of a society lies in how it treats its most vulnerable members. Whether he was chronicling boyhood shenanigans on the Mississippi, exposing the horrors of slavery, satirizing royal courts, or dissecting human nature in essay form, Twain's prose remains as vibrant, witty, and urgent today as it was over a century ago. Maxx, summarize our top recommended reading list for anyone looking to dive into Twain's catalog."
    ),
    (
        "maxx",
        "Maxx concluding our podcast rundown. If you're building your essential Mark Twain bookshelf, here is your definitive five-star reading order: First, Adventures of Huckleberry Finn—the foundational American novel that every reader must experience. Second, The Adventures of Tom Sawyer—for its humor, nostalgic charm, and sharp social observations. Third, Life on the Mississippi—for its vivid historical record of riverboat piloting and American expansion. Fourth, A Connecticut Yankee in King Arthur's Court—for its visionary mix of time-travel science fiction and social satire. And fifth, The Innocents Abroad—to enjoy Twain at his absolute funniest as a global travel correspondent. On behalf of the entire sovereign collective, thank you for joining us on this fifteen minute literary journey across the life and works of Mark Twain. The 3D stage on Port 8080 remains live, fully synchronized, and operational. Maxx signing off."
    )
]

def ensure_stage_server_and_ui():
    url = "http://127.0.0.1:8080/customer_app.html"
    is_running = False
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        res = s.connect_ex(("127.0.0.1", 8080))
        s.close()
        if res == 0:
            is_running = True
    except Exception:
        is_running = False

    if not is_running:
        server_script = os.path.join(SCRIPT_DIR, "stage_server.py")
        subprocess.Popen([sys.executable, server_script])
        time.sleep(1.5)

    print(f"[STAGE SERVER] Verified running on port 8080. Opening UI window: {url}")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    if os.name == 'nt':
        try:
            os.system(f'start {url}')
        except Exception:
            pass

def run_twain_podcast():
    try:
        ensure_stage_server_and_ui()
        print("=================================================================")
        print("[PODCAST] XORAS SOVEREIGN PODCAST: MARK TWAIN TOP READS (15 MIN)")
        print("[ENGINE] Voice Engine: Kokoro v1.0 ONNX via sync_stage_engine_kokoro.py")
        print("=================================================================")
        print("Stage Destination: http://127.0.0.1:8080/customer_app.html")
        print("=================================================================\n")
        sys.stdout.flush()

        start_time = time.time()
        target_duration = 15 * 60  # 15 minutes in seconds

        print("[ENGINE] Initializing Kokoro neural engine on main thread...")
        sys.stdout.flush()
        get_kokoro_engine()
        print("[ENGINE] Initialization complete. Starting 15-minute podcast broadcast.\n")
        sys.stdout.flush()

        turn_count = 0
        while time.time() - start_time < target_duration:
            for turn_idx, (agent_id, text) in enumerate(PODCAST_TURNS):
                if time.time() - start_time >= target_duration:
                    break

                turn_count += 1
                try:
                    payload = synthesize_kokoro_payload(agent_id, text)
                    elapsed = round((time.time() - start_time) / 60.0, 2)
                    print(f"[{elapsed} min] Turn {turn_count:02d} (Turn {turn_idx+1:02d}) | Speaker: {payload['agent'].upper()} ({payload['voice']}) | Duration: {round(payload['total_duration'], 1)}s")
                    sys.stdout.flush()

                    play_and_sync_payload(payload)
                except Exception as e:
                    import traceback
                    print(f"[ERROR] Turn {turn_idx+1} ({agent_id}) failed: {e}")
                    traceback.print_exc()
                    sys.stdout.flush()
                time.sleep(0.4)
        total_elapsed = round((time.time() - start_time) / 60.0, 2)
        print("\n=================================================================")
        print(f"[SUCCESS] 15-MINUTE MARK TWAIN PODCAST COMPLETED SUCCESSFULLY!")
        print(f"Total Spoken Time: {total_elapsed} minutes")
        print("=================================================================")
        sys.stdout.flush()
    except Exception as e:
        import traceback
        print(f"[ERROR] Podcast execution failed: {e}")
        traceback.print_exc()
        sys.stdout.flush()

if __name__ == "__main__":
    run_twain_podcast()
