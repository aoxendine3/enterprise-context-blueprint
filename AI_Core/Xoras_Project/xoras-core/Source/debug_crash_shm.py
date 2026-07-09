# --- DEBUG CRASH TEST SHM PRINTING ---
import sys
import os
import time
import asyncio
import signal

sys.path.append("/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core")
from Source.xoras_shm_bft import XorasShmBft

async def run_debug():
    print("Initializing cluster...")
    engine = XorasShmBft(num_nodes=16, num_byzantine=5, use_processes=True)
    time.sleep(0.5)
    
    print("Running Round 1...")
    await engine.run_consensus_round(True)
    
    print("Killing 3 nodes...")
    for node_id in [13, 14, 15]:
        pid = engine.processes[node_id].pid
        if pid:
            os.kill(pid, signal.SIGKILL)
    
    time.sleep(2.2)
    engine._update_heartbeats()
    print(f"Active nodes according to monitor: {engine.shm.buf[4]}")
    
    # Manually step through Round 2 and print SHM states
    engine.current_round_num = (engine.current_round_num + 1) % 250
    engine.shm.buf[300:engine.shm_size] = b'\x00' * (engine.shm_size - 300)
    engine.shm.buf[1] = 2 # True
    engine.shm.buf[3] = engine.current_round_num
    
    # 1. Trigger PREPARE
    print("\n--- Triggering PREPARE ---")
    engine.shm.buf[0] = 1
    time.sleep(0.5) # Wait half a second to let active processes write
    
    slot_size = 131
    prep_votes = []
    for i in range(16):
        start = 300 + (i * slot_size)
        prep_votes.append(engine.shm.buf[start])
    print(f"Prepare votes in SHM: {prep_votes}")
    
    # 2. Trigger COMMIT
    print("\n--- Triggering COMMIT ---")
    engine.shm.buf[0] = 2
    time.sleep(0.5)
    
    commit_votes = []
    for i in range(16):
        start = 300 + (i * slot_size)
        commit_votes.append(engine.shm.buf[start+65])
    print(f"Commit votes in SHM: {commit_votes}")
    
    # 3. Trigger FINALIZATION
    print("\n--- Triggering FINALIZATION ---")
    engine.shm.buf[0] = 3
    time.sleep(0.5)
    
    final_votes = []
    for i in range(16):
        start = 300 + (i * slot_size)
        final_votes.append(engine.shm.buf[start+130])
    print(f"Final committed values in SHM: {final_votes}")
    
    engine.cleanup()

if __name__ == "__main__":
    asyncio.run(run_debug())
