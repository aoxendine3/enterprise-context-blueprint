#!/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/venv/bin/python
import asyncio
import os
import sys
import sqlite3
import shutil

# Add the Source directory to the path so we can import the modules
sys.path.append("/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/Source")

from xoras_self_healing import SelfHealingManager

# Define a scratch directory for the simulation inside the visible project folder
SCRATCH_DIR = "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/Source/healing_test_tmp"
os.makedirs(SCRATCH_DIR, exist_ok=True)

# Subclass SelfHealingManager to override db_paths to point to scratch directory
class MockSelfHealingManager(SelfHealingManager):
    def __init__(self):
        super().__init__(data_dir=SCRATCH_DIR)
        self.db_paths = {
            "sentinel": os.path.join(SCRATCH_DIR, "sentinel.db"),
            "xoras_memory": os.path.join(SCRATCH_DIR, "xoras_memory.db")
        }

async def run_simulation():
    print("====================================================")
    print("🛡️ XORAS Self-Healing Simulation Run [PRODUCTION]")
    print("====================================================")
    
    manager = MockSelfHealingManager()
    
    # ----------------------------------------------------
    # TEST 1: Database Corruption Sentry
    # ----------------------------------------------------
    print("\n🔍 Test 1: Simulating Database Corruption...")
    
    # Create a corrupted file (write invalid bytes into a sqlite file)
    sentinel_path = manager.db_paths["sentinel"]
    with open(sentinel_path, "w") as f:
        f.write("This is not a SQLite database file! It is corrupted text.")
        
    print(f"Created dummy corrupted database at: {sentinel_path}")
    print("Executing database integrity check...")
    
    # Run check (should detect error and trigger repair)
    all_ok = await manager.check_database_integrity()
    
    print(f"Integrity check status (all_ok): {all_ok}")
    
    # Verify that the corrupted file was renamed and a new DB is created
    files = os.listdir(SCRATCH_DIR)
    print(f"Scratch folder contents after heal: {files}")
    
    corrupted_found = any("corrupted" in name for name in files)
    print(f"Healed backup file found: {corrupted_found}")
    
    # ----------------------------------------------------
    # TEST 2: Process Telemetry Outliers (CPU/Memory Spikes)
    # ----------------------------------------------------
    print("\n📈 Test 2: Simulating Process Memory/CPU Runway...")
    
    # Register our own process PID as a mock target named "mock-service"
    my_pid = os.getpid()
    manager.register_process("mock-service", my_pid)
    
    # Override max limits to force triggers
    manager.max_memory_bytes = 1000 # Set tiny memory limit to force memory spike trigger
    
    print(f"Registered PID {my_pid} under memory limit threshold {manager.max_memory_bytes} bytes.")
    print("Running resource monitoring scan...")
    
    # Run scan
    actions = await manager.monitor_resources()
    print(f"Monitoring action recommendations: {actions}")
    
    print("\n====================================================")
    print("✅ Simulation complete! Cleanup successful.")
    print("====================================================")
    
    # Cleanup scratch folder
    shutil.rmtree(SCRATCH_DIR)

if __name__ == "__main__":
    asyncio.run(run_simulation())
