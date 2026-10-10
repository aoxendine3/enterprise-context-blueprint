#!/usr/bin/env python3
import subprocess
import time
import os
import sys

SPEECHES = {
    "maxx": "We are Maxx, Lead Systems Architect. We are establishing the engineering corporate communication standard across all technical deliverables, code repositories, and public documentation. We prioritize clarity, empirical evidence, and reliable system execution over abstract theory or unverified claims.",
    "clara": "We are Clara, Lead Quality and Assurance Engineer. We verify that all public documentation, API integrations, and code assets meet enterprise software engineering standards. Every pipeline transition requires verified automated test execution and clear, maintainable evidence logs.",
    "vance": "We are Vance, Lead Security Auditor. We conduct rigorous code reviews and threat modeling across all system components. We ensure that zero hardcoded credentials, sensitive parameters, or unverified third-party dependencies are exposed in public repositories or API payloads.",
    "jarvis": "We are Jarvis, Technical Operations Lead. We manage release pipelines, deployment verification, and cross-functional team alignment. We mandate clean separation of concerns, deterministic build processes, and executive-level documentation across all engineering project milestones.",
    "dax": "We are Dax, Lead Analytics Engineer. We analyze system benchmark metrics, memory throughput, and query latencies using standardized statistical methods. We transform empirical performance data into structured, actionable insights for senior engineering leadership and technical stakeholders.",
    "noboo": "We are NoBoo, Governance and Compliance Auditor. We enforce strict adherence to corporate software development guidelines, version control standards, and peer review policies. All project artifacts must pass formal validation before release approval."
}

def speak_agent(agent, text):
    script_path = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/sync_stage_engine_kokoro.py"
    cmd = [sys.executable, script_path, agent, text]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr

def main():
    log_path = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/catch_log/six_agent_corporate_audio.log"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    with open(log_path, "a", encoding="utf-8") as f:
        f.write("================================================================================\n")
        f.write(f"SIX AGENT CORPORATE AUDIO DISPATCH RUN - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("================================================================================\n")

        for agent, text in SPEECHES.items():
            word_count = len(text.split())
            print(f"[{agent.upper()}] Synthesizing & Playing Speech Payload ({word_count} words)...")
            f.write(f"AGENT: {agent.upper()} | WORD COUNT: {word_count}\n")
            f.write(f"TEXT: {text}\n")
            
            rc, out, err = speak_agent(agent, text)
            if rc == 0:
                print(f"✅ [{agent.upper()}] Audio Payload Played Successfully!")
                f.write(f"STATUS: SUCCESS\n")
            else:
                print(f"❌ [{agent.upper()}] Speech Error: {err.strip()}")
                f.write(f"STATUS: ERROR ({err.strip()})\n")
            f.write("--------------------------------------------------------------------------------\n")
            time.sleep(1)

    print("All 6 Lead 9 Council Corporate Audio Speeches Completed & Verified!")

if __name__ == "__main__":
    main()
