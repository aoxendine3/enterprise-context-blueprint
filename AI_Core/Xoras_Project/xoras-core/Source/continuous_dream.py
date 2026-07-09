import os
import sys
import time
import asyncio
import sqlite3
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xoras_dream_simulator import (
    simulate_dream_cycle,
    save_dream_to_db,
    save_state_and_experiments,
    compress_dream_database,
    DREAM_DB_PATH
)

async def main():
    print("=== [XORAS 5-MINUTE CONTINUOUS BLACKBOX DREAMING CYCLE START] ===")
    start_time = time.time()
    duration = 300  # 5 minutes
    cycle = 0
    
    while time.time() - start_time < duration:
        cycle += 1
        print(f"\n[DREAM CYCLE #{cycle}]")
        
        # Simulate dream cycle as fast as possible
        dream = await simulate_dream_cycle()
        
        # Save to db
        save_dream_to_db(dream)
        
        # Save state and log
        save_state_and_experiments(dream, cycle)
        
        # Periodic database compaction to conserve space (every 5 cycles)
        if cycle % 5 == 0:
            print(f"\n--- Running periodic space conservation sweeps (Cycle #{cycle}) ---")
            compress_dream_database(max_threshold=12)
            
        # Small rest to avoid CPU thrashing
        await asyncio.sleep(0.1)
        
    print("\n=== [RUNNING FINAL DATABASE COMPACTION] ===")
    compress_dream_database(max_threshold=10)
    print("=== [XORAS 5-MINUTE BLACKBOX DREAMING CYCLE COMPLETE] ===")

if __name__ == "__main__":
    asyncio.run(main())
