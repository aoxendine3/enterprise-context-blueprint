import os
import sys
import time
import json
import signal
import subprocess
from typing import Dict, Any, Optional

STATE_PATH = "/tmp/xoras_state.json"
TEMP_STATE_PATH = "/tmp/xoras_state.json.tmp"

def write_state(state: Dict[str, Any]) -> None:
    """Atomically writes state to the state file using atomic renaming."""
    try:
        with open(TEMP_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(TEMP_STATE_PATH, STATE_PATH)
    except Exception as e:
        try:
            print(f"[STATE-WRITE] Error writing state: {e}")
            sys.stdout.flush()
        except OSError:
            pass

def read_state() -> Optional[Dict[str, Any]]:
    """Reads the state atomically from the state file."""
    if not os.path.exists(STATE_PATH):
        return None
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        try:
            print(f"[STATE-READ] Error reading state: {e}")
            sys.stdout.flush()
        except OSError:
            pass
        return None

def is_process_alive(pid: int) -> bool:
    """Checks if a process is active under the given PID and not in a zombie (Z) state on macOS."""
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    
    # Process exists in OS process table. Verify it is not a zombie (Z).
    try:
        state = subprocess.check_output(
            ["ps", "-p", str(pid), "-o", "state="], 
            stderr=subprocess.DEVNULL
        ).decode().strip()
        # Returns False if process is a zombie (has 'Z' status)
        return "Z" not in state and state != ""
    except Exception:
        # If status checks fail, assume process is dead
        return False

def run_primary(initial_state: Optional[Dict[str, Any]] = None) -> None:
    """Runs the primary system thread (simulating normal operation loop)."""
    pid = os.getpid()
    
    try:
        print(f"[PRIMARY] Active. Process ID: {pid}")
        sys.stdout.flush()
    except OSError:
        pass
    
    state = initial_state if initial_state else {
        "status": "INITIALIZED",
        "cycle_count": 0,
        "active_contexts": [],
        "last_update": time.time()
    }
    
    state["primary_pid"] = pid
    state["status"] = "RUNNING"
    
    write_state(state)
    
    try:
        while True:
            state["cycle_count"] += 1
            state["last_update"] = time.time()
            try:
                print(f"[PRIMARY] Operating cycle #{state['cycle_count']} | Updating State...")
                sys.stdout.flush()
            except OSError:
                pass
            write_state(state)
            time.sleep(1.0)
    except KeyboardInterrupt:
        state["status"] = "STOPPED"
        write_state(state)
        sys.exit(0)

def run_sentinel(primary_pid: int) -> None:
    """Runs the detached background sentinel monitor."""
    log_file = open("/tmp/sentinel.log", "a")
    sys.stdout = log_file
    sys.stderr = log_file
    
    print(f"[SENTINEL] Active. Monitoring Primary PID: {primary_pid}")
    log_file.flush()
    
    while True:
        time.sleep(0.1)
        
        if not is_process_alive(primary_pid):
            print(f"\n[SENTINEL] Alert! Primary process {primary_pid} has died or entered zombie state.")
            log_file.flush()
            
            # Retrieve last stable state
            state = read_state()
            print(f"[SENTINEL] Ingesting state recovery payload: {state}")
            log_file.flush()
            
            # Reboot primary process, explicitly redirecting output to avoid SIGPIPE
            cmd = [sys.executable, "-u", __file__, "--resume"]
            
            log_fd = os.open("/tmp/new_primary.log", os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
            p = subprocess.Popen(cmd, stdout=log_fd, stderr=log_fd, start_new_session=True)
            os.close(log_fd)
            
            new_pid = p.pid
            print(f"[SENTINEL] Successfully spawned new Primary under process ID: {new_pid}")
            log_file.flush()
            
            primary_pid = new_pid
            
            if state:
                state["primary_pid"] = new_pid
                state["status"] = "RECOVERED"
                write_state(state)

def main() -> None:
    if "--resume" in sys.argv:
        state = read_state()
        run_primary(initial_state=state)
    elif "--sentinel" in sys.argv:
        try:
            pid_idx = sys.argv.index("--sentinel") + 1
            target_pid = int(sys.argv[pid_idx])
            run_sentinel(target_pid)
        except (ValueError, IndexError):
            sys.exit(1)
    else:
        pid = os.getpid()
        
        # Spawn sentinel completely detached from stdout/stderr, running in unbuffered mode
        sentinel_cmd = [sys.executable, "-u", __file__, "--sentinel", str(pid)]
        subprocess.Popen(
            sentinel_cmd, 
            start_new_session=True, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        
        run_primary()

if __name__ == "__main__":
    main()
