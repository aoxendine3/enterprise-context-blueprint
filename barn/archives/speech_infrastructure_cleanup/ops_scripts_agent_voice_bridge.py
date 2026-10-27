#!/usr/bin/env python3
"""
XORAS::OS Agent Voice Bridge
--------------------------------
This script wires the live multi‑model debate output from the native Rust
`xoras_conductor` binary into the audio pipeline (`agent_speak.sh`).
It reads the conductor's stdout line‑by‑line, extracts the agent name and
spoken payload, then dispatches a hardware‑locked audio message for each
turn. The bridge runs until the conductor exits.

Design goals:
* Zero‑overlap audio – each turn acquires the POSIX advisory lock
  (`/tmp/xoras_speech.lock`) before invoking `agent_speak.sh`.
* Fault‑tolerant – if an unexpected line is encountered it is logged but
  does not abort the bridge.
* Simple – pure Python glue (acceptable because it does not replace any
  core runtime component, only orchestrates already compiled Rust).
"""
import subprocess
import re
import os
import sys
import threading
import time

# Path to the compiled Rust conductor binary (release build)
CONDUCTOR_BIN = os.path.abspath(
    "../src/xoras_conductor/target/release/xoras_conductor"
)

# Path to the agent speak helper script. The repository now contains a symlink
# `ops/scripts/agent_speak.sh` that resolves to the correct location.
AGENT_SPEAK = os.path.abspath("../../../ops/scripts/agent_speak.sh")

# Regular expression to capture agent name and spoken text from the conductor
# output. Example line:
# "[VANCE] Lock acquired. Streaming: 'DAXX, your HexCell stride …'"
AGENT_LINE_RE = re.compile(r"\[(?P<agent>[^\]]+)\].*Streaming: '(?P<msg>.*)'")

def speak(agent: str, message: str):
    """Invoke the native audio bridge for a given agent.

    The agent identifier is lower‑cased to match the allowlist in
    `agent_speak.sh` (maxx, clara, vance, dax). If an unknown agent is
    supplied the call will fail, which is acceptable – the bridge will log
    the error and continue.
    """
    cmd = ["bash", AGENT_SPEAK, agent.lower(), message]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"[voice_bridge] audio dispatch failed for {agent}: {e}\n")

def run_conductor():
    """Spawn the Rust conductor and stream its stdout.

    The subprocess is launched with `universal_newlines=True` so we receive
    text lines. Each line is examined; if it matches the agent pattern the
    corresponding audio is emitted.
    """
    proc = subprocess.Popen(
        [CONDUCTOR_BIN],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    if proc.stdout is None:
        sys.stderr.write("[voice_bridge] conductor stdout not available\n")
        return
    for raw_line in proc.stdout:
        line = raw_line.strip()
        if not line:
            continue
        # Debug output – useful during integration but suppressed in production
        # print(f"[voice_bridge] raw: {line}")
        m = AGENT_LINE_RE.search(line)
        if m:
            agent = m.group("agent")
            msg = m.group("msg")
            speak(agent, msg)
        else:
            # Non‑agent lines (e.g., initialization messages) are ignored.
            continue
    proc.wait()
    return proc.returncode

if __name__ == "__main__":
    # Ensure the script is executable and the lock file exists.
    lock_path = "/tmp/xoras_speech.lock"
    # Touch the lock file so `flock` operations succeed.
    open(lock_path, "a").close()
    exit_code = run_conductor()
    sys.exit(exit_code)
