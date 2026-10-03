import sys
with open('/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/media_director_agent.py', 'r') as f:
    content = f.read()

content = content.replace('''    if rejected:
        return 2

    cmd = [sys.executable, MONITOR_SCRIPT, agent_id, text]
    completed = subprocess.run(cmd, check=False, stdin=subprocess.DEVNULL)
    return completed.returncode''', '''    if rejected:
        return 2

    FIFO_PATH = "/tmp/kokoro_speech_fifo"
    import os
    if os.path.exists(FIFO_PATH):
        try:
            with open(FIFO_PATH, "w") as fifo:
                fifo.write(json.dumps({"agent": agent_id, "text": text}) + "\\n")
            return 0
        except Exception:
            pass

    cmd = [sys.executable, MONITOR_SCRIPT, agent_id, text]
    completed = subprocess.run(cmd, check=False, stdin=subprocess.DEVNULL)
    return completed.returncode''')

with open('/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/media_director_agent.py', 'w') as f:
    f.write(content)
