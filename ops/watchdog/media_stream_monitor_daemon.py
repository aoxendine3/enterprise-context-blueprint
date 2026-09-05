"""
XORAS MEDIA STREAM MONITOR: NATIVE COMPILED GATEKEEPER INTEGRATION
Golden List Asset #002: Kernel-Level Audio Mutex with Stale PID Self-Healing
Guarantees ZERO audio overlap via native Apple Silicon ARM64 binary.
"""
import os, sys, time, subprocess

GATEKEEPER_BIN = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/capabilities/sovereign_systems_core/bin/sovereign_gatekeeper"
SYNC_STAGE_ENGINE = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/sync_stage_engine.py"

def sanitize_input(text):
    if not text:
        return "Standing by."
    clean = "".join(ch for ch in text if ch in ('\n', '\t', ' ') or ord(ch) >= 32)
    return clean.strip() or "Standing by."

def run_isolated_stream(agent_id, text):
    text = sanitize_input(text)
    agent_id = sanitize_input(agent_id).lower()

    # 1. Acquire exclusive lock via compiled Rust kernel gatekeeper
    res = subprocess.run([GATEKEEPER_BIN, "acquire", agent_id, "120000"], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[MEDIA_MONITOR_ERROR] Gatekeeper acquisition failed: {res.stderr.strip()}", file=sys.stderr)
        return

    try:
        lock_file = "/tmp/sovereign_audio_kernel.lock"
        if os.path.exists(lock_file):
            with open(lock_file, "w") as f:
                f.write(f"{os.getpid()}\n{agent_id}\n{int(time.time())}\n")
    except Exception:
        pass

    try:
        turns = []
        if os.path.exists(text) and (text.endswith(".json") or text.endswith(".txt")):
            try:
                with open(text) as f:
                    content = f.read().strip()
                if content.startswith("[") and content.endswith("]"):
                    import json
                    turns = json.loads(content)
            except Exception:
                pass
        elif text.startswith("[") and text.endswith("]"):
            try:
                import json
                turns = json.loads(text)
            except Exception:
                pass

        if turns:
            sys.path.insert(0, "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui")
            from sync_stage_engine import speak_with_word_sync
            for turn in turns:
                spk = turn.get("agent", agent_id).lower()
                utt = turn.get("text", "")
                if utt:
                    speak_with_word_sync(spk, utt)
                    time.sleep(0.4)
        else:
            cmd = ["python3", SYNC_STAGE_ENGINE, agent_id, text]
            subprocess.run(cmd, check=True)

        time.sleep(0.1)
    finally:
        try:
            subprocess.run([GATEKEEPER_BIN, "release"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            try:
                if os.path.exists("/tmp/sovereign_audio_kernel.lock"):
                    os.remove("/tmp/sovereign_audio_kernel.lock")
            except Exception:
                pass

if __name__ == "__main__":
    ag = sys.argv[1] if len(sys.argv) > 1 else "maxx"
    tx = sys.argv[2] if len(sys.argv) > 2 else "Operational."
    run_isolated_stream(ag, tx)
