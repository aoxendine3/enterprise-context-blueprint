import tracemalloc
import gc
import sys
import os
import logging
import threading
import time
import inspect
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("XorasMemoryLeakDetector")

class XorasMemoryProfiler:
    """
    Tier 7 Performance Module. 
    Traces memory allocations and detects potential leaks in dynamic Python agent scripts
    using native tracemalloc auditing.
    """
    def __init__(self):
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        logger.info("Tracemalloc instrumentation active.")

    def collect_garbage(self):
        """Forces immediate garbage collection to clear transient allocations."""
        gc.collect()

    def get_snapshot(self) -> tracemalloc.Snapshot:
        """Takes a clean memory allocation snapshot."""
        self.collect_garbage()
        return tracemalloc.take_snapshot()

    def get_referrers_chain(self, obj: Any, max_depth: int = 3) -> List[str]:
        """
        Performs Reference Chain Analysis.
        Traverses garbage collector references to find what is keeping an object alive in memory.
        """
        chain = []
        current = obj
        for depth in range(max_depth):
            referrers = gc.get_referrers(current)
            # Find the most relevant referrer (ignoring internal lists and frames)
            next_ref = None
            for ref in referrers:
                if ref is referrers or ref is sys._getframe() or isinstance(ref, (list, dict)) and len(ref) == 0:
                    continue
                # If referrer is a module, class, or dict
                if inspect.ismodule(ref):
                    chain.append(f"Module: {ref.__name__}")
                    next_ref = ref
                    break
                elif inspect.isclass(ref):
                    chain.append(f"Class: {ref.__name__}")
                    next_ref = ref
                    break
                elif isinstance(ref, dict):
                    # Check if it's a class or instance namespace
                    if "__declared_fields__" in ref or "__module__" in ref:
                        chain.append("Class Namespace Dict")
                    else:
                        chain.append("Dict Namespace")
                    next_ref = ref
                    break
                elif isinstance(ref, list):
                    chain.append(f"List (len: {len(ref)})")
                    next_ref = ref
                    break
            
            if next_ref is None or next_ref is current:
                break
            current = next_ref
        
        return chain

    def compare_snapshots(self, baseline: tracemalloc.Snapshot, target: tracemalloc.Snapshot, limit: int = 10):
        """Compares baseline and target snapshots to pinpoint top memory leaks."""
        stats = target.compare_to(baseline, 'lineno')
        
        print("\n==================================================")
        print("     XORAS MEMORY LEAK DIAGNOSTIC REPORT         ")
        print("==================================================")
        print(f"Top {limit} growing memory allocations:")
        
        total_increase = 0
        for index, stat in enumerate(stats[:limit]):
            frame = stat.traceback[0]
            # Exclude standard library internals from cluttering report
            if "tracemalloc" in frame.filename or "importlib" in frame.filename or "threading" in frame.filename:
                continue
            
            size_diff_kb = stat.size_diff / 1024
            total_increase += stat.size_diff
            
            # Format file name for readability
            short_filename = Path(frame.filename).name
            print(f"[{index + 1}] {short_filename}:{frame.lineno} -> +{size_diff_kb:.2f} KB (total size: {stat.size / 1024:.2f} KB)")
        
        print("--------------------------------------------------")
        print(f"Cumulative Leak Footprint: {total_increase / 1024:.2f} KB")
        print("==================================================\n")

class MemoryLeakDaemon(threading.Thread):
    """
    Continuous Heartbeat Memory Watchdog. Runs as a background daemon,
    periodically checking process memory growth and calculating leak rate slopes.
    """
    def __init__(self, check_interval_sec: float = 1.0, leak_threshold_kb_sec: float = 50.0):
        super().__init__()
        self.daemon = True
        self.check_interval_sec = check_interval_sec
        self.leak_threshold_kb_sec = leak_threshold_kb_sec
        self.history: List[Tuple[float, float]] = [] # list of (timestamp, memory_kb)
        self.running = False
        self.profiler = XorasMemoryProfiler()

    def get_process_memory_kb(self) -> float:
        """Retrieves process resident memory size directly from the OS."""
        try:
            # Query RSS via ps
            res = subprocess.run(["ps", "-o", "rss=", "-p", str(os.getpid())], capture_output=True, text=True)
            if res.returncode == 0:
                return float(res.stdout.strip())
        except Exception:
            pass
        return 0.0

    def run(self):
        logger.info("[DAEMON] Starting background memory leak watchdog...")
        self.running = True
        baseline_snapshot = self.profiler.get_snapshot()
        
        while self.running:
            time.sleep(self.check_interval_sec)
            self.profiler.collect_garbage()
            
            current_mem = self.get_process_memory_kb()
            current_time = time.time()
            self.history.append((current_time, current_mem))
            
            # Maintain 20-sample history window
            if len(self.history) > 20:
                self.history.pop(0)
                
            # Perform linear regression to calculate growth rate slope
            if len(self.history) >= 5:
                n = len(self.history)
                sum_x = sum(t[0] for t in self.history)
                sum_y = sum(t[1] for t in self.history)
                sum_xx = sum(t[0]**2 for t in self.history)
                sum_xy = sum(t[0]*t[1] for t in self.history)
                
                denominator = (n * sum_xx - sum_x**2)
                if denominator != 0:
                    slope = (n * sum_xy - sum_x * sum_y) / denominator
                    # Slope represents KB growth per second
                    if slope > self.leak_threshold_kb_sec:
                        logger.warning(f"[DAEMON] WARNING: Memory leak slope detected! Growth rate: {slope:.2f} KB/sec.")
                        target_snapshot = self.profiler.get_snapshot()
                        self.profiler.compare_snapshots(baseline_snapshot, target_snapshot, limit=5)
                        # Reset baseline to avoid redundant alerts
                        baseline_snapshot = target_snapshot

    def stop(self):
        self.running = False

if __name__ == "__main__":
    # Start the memory watchdog daemon to run indefinitely in the background
    daemon = MemoryLeakDaemon(check_interval_sec=5.0, leak_threshold_kb_sec=100.0)
    daemon.start()
    
    logger.info("Memory watchdog active. Running background monitoring loop...")
    try:
        while True:
            time.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopping watchdog...")
        daemon.stop()

