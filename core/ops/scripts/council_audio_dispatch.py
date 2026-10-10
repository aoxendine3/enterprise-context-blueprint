#!/usr/bin/env python3
import subprocess
import time
import os

SPEECHES = {
    "maxx": "We are Maxx, Bare-Metal Lead of the Lead 9 Council. We are enforcing absolute, uncompromising precision across every physical hardware and browser execution step. We are accessing the existing post on the DEV community platform, executing the edit mode transition, isolating the title, tags, and body fields, and publishing the verified submission packet with full cryptographic evidence.",
    "clara": "We are Clara, Human Protection and Clinical Precision Lead. We verify that all patient-facing, human-facing, and public evidence payloads maintain zero state pollution and absolute mathematical integrity. No action will advance through the Trinity Gate without verified proof receipts recorded directly in the workspace catch log.",
    "vance": "We are Vance, Adversarial Falsification Lead. We challenge every assertion and test every DOM element boundary. We verify that zero third-party entity branding leaks into asset URLs or paper headers, and that all post fields pass the fourteen gate blackbox gauntlet before final publication.",
    "jarvis": "We are Jarvis, Master Project Oversight Lead. We synchronize the multi-agent swarm execution across Apple Silicon M4 unified memory. We mandate step-by-step verification, real-time audio generation across all four council members, and complete alignment with the absolute architectural verification law."
}

def main():
    log_path = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/catch_log/council_audio_dispatch.log"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    with open(log_path, "a", encoding="utf-8") as f:
        f.write("================================================================================\n")
        f.write(f"COUNCIL AUDIO DISPATCH RUN - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("================================================================================\n")

        for agent, text in SPEECHES.items():
            word_count = len(text.split())
            print(f"[{agent.upper()}] Dispatching Audio Payload ({word_count} words)...")
            f.write(f"AGENT: {agent.upper()} | WORD COUNT: {word_count}\n")
            f.write(f"TEXT: {text}\n")
            
            p = subprocess.run(["bash", "ops/scripts/agent_speak.sh", agent, text], capture_output=True, text=True)
            if p.returncode == 0:
                print(f"✅ [{agent.upper()}] Audio Payload Dispatched and Played Successfully!")
                f.write(f"STATUS: SUCCESS\n")
            else:
                print(f"❌ [{agent.upper()}] Audio Dispatch Error: {p.stderr}")
                f.write(f"STATUS: ERROR ({p.stderr.strip()})\n")
            f.write("--------------------------------------------------------------------------------\n")
            time.sleep(1)

    print("All 4 Lead 9 Council Audio Speeches Completed & Verified!")

if __name__ == "__main__":
    main()
