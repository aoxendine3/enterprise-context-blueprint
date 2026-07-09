import os
import json
import time
import signal
import subprocess
import sys

STATE_FILE = "xoras_state.json"
MAX_TRADES_PER_SEC = 10


def find_omnicore_pid():
    """Finds the PID of the Omni-Core daemon."""
    try:
        # Use pgrep to find the python3 process running xoras_omni_core.py
        output = subprocess.check_output(
            ["pgrep", "-f", "xoras_omni_core.py"]).decode().strip()
        pids = [int(p) for p in output.split('\n') if p]
        # Avoid killing ourselves if our filename matches somehow
        pids = [p for p in pids if p != os.getpid()]
        return pids[0] if pids else None
    except subprocess.CalledProcessError:
        return None


def kill_omnicore(reason):
    """Executes the raw OS-level SIGKILL."""
    pid = find_omnicore_pid()
    if pid:
        print(f"\n[KILL-SWITCH] DEAD MAN'S SWITCH TRIGGERED: {reason}")
        print(f"[KILL-SWITCH] Executing OS-Level SIGKILL on PID: {pid}")
        try:
            os.kill(pid, signal.SIGKILL)
            print("[KILL-SWITCH] Omni-Core process successfully destroyed.")
        except ProcessLookupError:
            print("[KILL-SWITCH] Process already dead.")
    else:
        print(f"\n[KILL-SWITCH] Omni-Core not found. Reason: {reason}")
    sys.exit(0)


def arm_switch():
    print("==========================================")
    print("     XORAS DEAD MAN'S SWITCH (ARMED)      ")
    print("==========================================")
    print("Monitoring Omni-Core execution telemetry...")

    last_trades = 0
    last_timestamp = time.time()

    while True:
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, "r") as f:
                    state = json.load(f)

                current_trades = state.get("active_trades", 0)
                current_time = state.get("timestamp", time.time())

                time_delta = current_time - last_timestamp
                trade_delta = current_trades - last_trades

                if time_delta > 0:
                    velocity = trade_delta / time_delta
                    if velocity > MAX_TRADES_PER_SEC:
                        kill_omnicore(
                            f"Velocity breached. {velocity:.2f} trades/sec detected.")

                last_trades = current_trades
                last_timestamp = current_time

            # If the hard-lock override file is created, kill it immediately
            if os.path.exists("kill.override"):
                os.remove("kill.override")
                kill_omnicore("Hard-lock manual override triggered.")

        except json.JSONDecodeError:
            pass  # File being written to
        except Exception as e:
            pass

        time.sleep(0.1)  # Check state at 10Hz


if __name__ == "__main__":
    arm_switch()
