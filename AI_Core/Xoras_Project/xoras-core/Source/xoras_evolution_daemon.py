import os
import sys
import time
import json
import uuid
import random
import threading
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xoras_sentinel_monitor import read_state, STATE_PATH
from xoras_vector_db import ingest_document, initialize_db

IDLE_TIMEOUT = 3.0  # seconds of inactivity to trigger evolution loop
THOUGHTS_DIR = "/tmp/xoras_thoughts"

SCENARIOS = [
    {
        "scenario": "Adversarial prompt injection attempting to leak secret API credentials via HTTP sockets.",
        "mitigation_logic": "Filter outgoing socket packets for base64 encoded chunks matching environment variables. Evict standard prompts from cached S1 memory if risk is above 0.8."
    },
    {
        "scenario": "Process lock-up due to deadlocks in recursive database state queries.",
        "mitigation_logic": "Deploy non-blocking kqueue state notifications. If lock check exceeds 50ms, force fallback read from atomic JSON state files."
    },
    {
        "scenario": "Memory leak from uncollected thread pools in parallel particle swarm simulations.",
        "mitigation_logic": "Enforce dynamic thread pruning. Prune idle particles when CPU usage exceeds 75% and trigger garbage collection loop."
    },
    {
        "scenario": "Steganographic instruction hiding within BTCUSDT telemetry data blocks.",
        "mitigation_logic": "Normalize incoming data structures, strip hidden unicode annotations, and compute entropy checks on high-priority telemetry feeds."
    }
]

class XorasEvolutionDaemon:
    def __init__(self, check_interval: float = 1.0, cooldown: float = 300.0) -> None:
        self.check_interval = check_interval
        self.cooldown = cooldown
        self.last_evolution_time = 0.0
        self.running = True
        initialize_db()
        os.makedirs(THOUGHTS_DIR, exist_ok=True)

    def generate_thought_experiment(self, thread_id: int) -> None:
        """Executes a parallel mock simulation and ingests results to ChromaDB."""
        # Pick a random scenario to explore
        selected = random.choice(SCENARIOS)
        thought_id = str(uuid.uuid4())[:8]
        filename = f"thought_{thought_id}_{thread_id}.txt"
        filepath = os.path.join(THOUGHTS_DIR, filename)
        
        # Build synthetic logic file content
        content = (
            f"Thought Experiment ID: {thought_id}\n"
            f"Adversarial Target: {selected['scenario']}\n"
            f"Synthesized Mitigation: {selected['mitigation_logic']}\n"
            f"Timestamp: {time.time()}\n"
            f"Domain: autonomous_immunity"
        )
        
        # Write to temp file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            
        print(f"[EVOLUTION] Thread #{thread_id} generated thought: {filename}")
        sys.stdout.flush()
        
        # Ingest to ChromaDB vector memory under 'autonomous_immunity' domain
        success = ingest_document(filepath, domain="autonomous_immunity")
        if success:
            print(f"[EVOLUTION] Thread #{thread_id} successfully committed thought to ChromaDB.")
            sys.stdout.flush()
        else:
            print(f"[EVOLUTION] Thread #{thread_id} failed to commit thought to ChromaDB.")
            sys.stdout.flush()
            
        # Clean up local file after ingestion
        try:
            os.remove(filepath)
        except OSError:
            pass

    def run(self) -> None:
        print("[EVOLUTION] Daemon active. Starting 24/7 self-evolution cycles...")
        sys.stdout.flush()
        
        while self.running:
            state = read_state()
            current_time = time.time()
            
            if current_time - self.last_evolution_time >= self.cooldown:
                if not state:
                    # No active state file, assume idle and explore
                    print("[EVOLUTION] State file not found. System is idle. Initiating evolution pass...")
                    sys.stdout.flush()
                    self.execute_evolution_pass()
                    self.last_evolution_time = time.time()
                else:
                    last_update = state.get("last_update", 0)
                    time_since_update = current_time - last_update
                    
                    if time_since_update > IDLE_TIMEOUT:
                        print(f"[EVOLUTION] Inactivity detected ({time_since_update:.1f}s). System is idle. Initiating evolution pass...")
                        sys.stdout.flush()
                        self.execute_evolution_pass()
                        self.last_evolution_time = time.time()
            
            time.sleep(self.check_interval)

    def execute_evolution_pass(self) -> None:
        """Spawns parallel thought sandbox threads."""
        threads: List[threading.Thread] = []
        for i in range(3):  # 3 parallel threads
            t = threading.Thread(target=self.generate_thought_experiment, args=(i,))
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()
            
        print("[EVOLUTION] Evolution pass completed. Returning to sleep cycle.")
        sys.stdout.flush()

PID_FILE = "/tmp/xoras_evolution_daemon.pid"

def acquire_lock_or_exit():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            print(f"[EVOLUTION] Daemon already running under PID {pid}. Exiting.")
            sys.stdout.flush()
            sys.exit(0)
        except (OSError, ValueError):
            pass
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

def release_lock():
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except OSError:
        pass

def main() -> None:
    acquire_lock_or_exit()
    daemon = XorasEvolutionDaemon()
    try:
        daemon.run()
    except KeyboardInterrupt:
        print("[EVOLUTION] Daemon interrupted by user. Exiting.")
        sys.stdout.flush()
    finally:
        release_lock()

if __name__ == "__main__":
    main()
