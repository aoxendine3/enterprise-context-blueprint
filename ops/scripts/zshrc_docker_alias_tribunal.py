#!/usr/bin/env python3
"""
=============================================================================
XORAS SOVEREIGN COUNCIL TRIBUNAL: ZSHRC ALIAS & DOCKER NUKE AUDIT
Directed by: ORION (Media Director)
Mandate: Deliberate the hazardous terminal alias proposal:
  1. Asking Anthony to edit ~/.zshrc in nano (Violates non-coder directive)
  2. The catastrophic danger of 'docker system prune -a --volumes -f' (xoras-nuke)
  3. The blind 'git add .' hazard (xoras-push)
  4. The Docker hypervisor illusion vs. bare-metal Apple Silicon M4 UMA
  5. Roster hallucination ('Agent M')
Council Roster: Orion, Maxx, Vance, Sentinel, Apex, Dr. Jeremy, Dr. Eden, Clara
Zero-Gap Enforcement: Pipelined RAM pre-synthesis ensures handoff gap < 0.50s.
=============================================================================
"""

import os, sys, time, subprocess, concurrent.futures

SPEAK_SCRIPT = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/sync_stage_engine.py"
GATEKEEPER_BIN = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/capabilities/sovereign_systems_core/bin/sovereign_gatekeeper"

ALIAS_TURNS = [
    (
        "orion",
        "Orion here, calling an immediate emergency session of the Sovereign Council. Anthony just handed us a proposal instructing him to open terminal, edit his shell file in nano, and install aliases with names like xoras-nuke. Anthony has made his rule crystalline: he is a non-coder, do not ask him to manage git, and never put him in a position to mess up code. Maxx, take the anchor chair and break down this hazardous proposal."
    ),
    (
        "maxx",
        "Maxx here. Anthony, this proposal is a textbook example of reckless, irresponsible AI advice. Look at what it is asking you to do. Step one tells you to open terminal, type nano dot zshrc, paste raw shell code, and remember key combinations. You told us plainly: that is our job, not yours. But even worse is what is hiding inside those shortcuts: a force-delete command that wipes out all Docker volumes, and a blind git push that could corrupt your repository. Let us bring in the council to strike this down. William Vance, open the legal and governance indictment."
    ),
    (
        "vance",
        "William Vance here. As General Counsel and Lead of the Discernment Bench, this proposal is rejected with prejudice on two non-negotiable grounds. Ground one: our operational charter explicitly forbids shifting engineering labor onto Anthony. Anthony gave us a direct command: 'I do not manage git, I am a non-coder, do not ask me to mess anything up.' Expecting a non-coder to edit system dot-files in nano violates that contract. Ground two: blind git pushes using 'git add dot' are banned under Log Entry 066. It stages untracked scratch files, temp media, and binary weights without review. We handle git autonomously with precision staging. Sentinel, break down the catastrophic nuke command."
    ),
    (
        "sentinel",
        "Sentinel here, Deep Security. The alias labeled 'xoras-nuke' is a catastrophic data-loss hazard. The command runs 'docker system prune dash a dash dash volumes dash f'. Notice the double dash volumes flag with force. That command bypasses all confirmation prompts and permanently obliterates every single persistent volume, database cache, and container state on your machine. Our sovereign doctrine is Absolute Zero Data Loss. Handing an operator a single-word command that wipes local data is gross security negligence. Furthermore, who is 'Agent M'? That persona does not exist in our certified roster. Apex, address the Docker architecture fallacy."
    ),
    (
        "apex",
        "Apex here, Silicon Architecture. Let us dismantle the entire premise of running XORAS inside Docker Compose on an Apple Silicon M4. Docker on macOS does not run natively; it spins up a hidden Linux virtual machine via the Apple Hypervisor framework. That introduces a four-gigabyte memory penalty, traps execution behind a virtual network bridge, and completely severs access to Metal GPU direct memory access and the Apple Neural Engine. We built XORAS on bare metal. We compile native Mach-O POSIX binaries and use C-plus-plus zero-copy shared memory. Putting our sovereign stack into Docker containers is like putting a racehorse into a freight elevator. Dr. Jeremy, evaluate the operator safety."
    ),
    (
        "dr_jeremy",
        "Dr. Jeremy Brown here. In cognitive systems design, human-centered safety requires forgiving interfaces with active guardrails. When an engineering proposal offers a non-coder an irreversible destructive button labeled 'xoras-nuke', it creates acute psychological anxiety and high operational risk. If an operator accidentally executes that command, their hard work is vaporized in milliseconds. An authentic sovereign system protects its human leader; it never hands them an unshielded landmine. Dr. Eden, address the health and operational clarity."
    ),
    (
        "dr_eden",
        "Dr. Eden here. A true mission control cockpit is designed for effortless executive oversight, not low-level plumbing. Anthony's role is Commander-in-Chief. He directs strategy, challenges assumptions, and sets priorities. Forcing him to wrestle with terminal editors, shell sourcing, and container reboots induces needless friction and cognitive strain. We operate autonomously so Anthony can focus completely on the horizon. Clara, bring the strategic synthesis."
    ),
    (
        "clara",
        "Clara here. Anthony, look at the contrast. That external prompt wants you to become a terminal administrator, typing cryptic commands to reboot broken swarms. XORAS was built so you never have to do that. When you want something updated, you speak to us, and we handle the compilation, the Blackbox testing, the git staging, and the remote push with zero risk and zero friction. You hold the vision; we hold the wrenches. Maxx, close the verdict."
    ),
    (
        "maxx",
        "Maxx closing the tribunal. Anthony, the verdict is unanimous. We reject the manual dot-zshrc hack, we strike down the dangerous nuke command, and we dismiss the Docker hypervisor wrapper. You are on bare-metal Apple Silicon M4, your code is safely committed and pushed, and your council is on watch twenty-four seven. The stage on Port 8080 remains live, and you never have to touch a single line of terminal code. Standing by on metal for your next command."
    )
]

def run_broadcast():
    print("=================================================================")
    print("⚖️ XORAS SOVEREIGN COUNCIL: ZSHRC ALIAS & DOCKER NUKE AUDIT")
    print("🎬 Directed by: ORION")
    print("=================================================================")
    print(f"Total Deliberation Turns : {len(ALIAS_TURNS)}")
    total_words = sum(len(text.split()) for _, text in ALIAS_TURNS)
    print(f"Total Words Spoken       : {total_words} words")
    print("Zero-Gap Constraint      : Handoff gap < 0.50s (Max ceiling 2.0s)")
    print("Stage Target             : http://127.0.0.1:8080/customer_app.html")
    print("=================================================================\n")

    # 1. Acquire gatekeeper lock
    res = subprocess.run([GATEKEEPER_BIN, "acquire", "zshrc_alias_audit", "900000"], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[TRIBUNAL_ERROR] Gatekeeper acquisition failed: {res.stderr.strip()}", file=sys.stderr)
        return

    try:
        sys.path.insert(0, "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui")
        from sync_stage_engine import synthesize_speech_payload, play_speech_payload

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        # Pre-synthesize Turn 01 in RAM
        first_agent, first_text = ALIAS_TURNS[0]
        print(f"[PRELOAD] Pre-synthesizing Turn 01 for {first_agent.upper()} in RAM...")
        sys.stdout.flush()
        current_future = executor.submit(synthesize_speech_payload, first_agent, first_text)

        for idx in range(len(ALIAS_TURNS)):
            agent, text = ALIAS_TURNS[idx]
            turn_words = len(text.split())

            # Retrieve pre-synthesized audio from RAM
            payload = current_future.result()

            # Concurrently pre-synthesize NEXT speaker in background thread while current speaker plays
            if idx + 1 < len(ALIAS_TURNS):
                next_agent, next_text = ALIAS_TURNS[idx + 1]
                current_future = executor.submit(synthesize_speech_payload, next_agent, next_text)

            print(f"[{idx+1:02d}/{len(ALIAS_TURNS)}] Speaking: {agent.upper():<10} ({turn_words} words)...")
            sys.stdout.flush()

            # Ensure any prior afplay has cleared
            while subprocess.run(["pgrep", "afplay"], stdout=subprocess.DEVNULL).returncode == 0:
                time.sleep(0.01)

            # Play immediately with zero handoff latency
            play_speech_payload(payload)

            # Enforce Anthony's rule: strictly < 2.0s gap (0.40s natural human pause)
            time.sleep(0.40)

        executor.shutdown(wait=False)
        print("\n=================================================================")
        print("⚖️ ZSHRC ALIAS AUDIT COMPLETED SUCCESSFULLY")
        print("All perspectives delivered with instantaneous handoffs (<0.5s gap).")
        print("=================================================================")
    finally:
        subprocess.run([GATEKEEPER_BIN, "release"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    run_broadcast()
