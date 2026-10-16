import threading
import time
import json
import resource

HEXCELL_SLOTS = 6
TOTAL_OPS = 1000000
NUM_THREADS = 8
OPS_PER_THREAD = TOTAL_OPS // NUM_THREADS

class HexCellRingPy:
    def __init__(self):
        self.lock = threading.Lock()
        self.active_slots = [0] * HEXCELL_SLOTS
        self.shadow_slots = [0] * HEXCELL_SLOTS
        self.total_committed = 0
        self.total_compensated = 0
        self.contention_retries = 0

    def execute_saga(self, slot: int, tx_id: int, new_val: int) -> bool:
        with self.lock:
            initial = self.active_slots[slot]
            self.shadow_slots[slot] = new_val

            # Optimistic simulation under lock
            self.active_slots[slot] = new_val
            self.total_committed += 1
            return True

def worker(tid: int, ring: HexCellRingPy):
    start_tx = tid * OPS_PER_THREAD + 1
    for i in range(OPS_PER_THREAD):
        tx_id = start_tx + i
        slot = tx_id % HEXCELL_SLOTS
        new_val = 0xBEAF000000000000 | tx_id
        ring.execute_saga(slot, tx_id, new_val)

def main():
    ring = HexCellRingPy()
    threads = []

    t0 = time.perf_counter()

    for tid in range(NUM_THREADS):
        t = threading.Thread(target=worker, args=(tid, ring))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    t_end = time.perf_counter()
    elapsed_sec = t_end - t0
    ops_sec = TOTAL_OPS / elapsed_sec
    avg_latency_ns = (elapsed_sec / TOTAL_OPS) * 1e9

    usage = resource.getrusage(resource.RUSAGE_SELF)
    import platform
    if platform.system() == "Darwin":
        rss_mb = usage.ru_maxrss / (1024.0 * 1024.0)
    else:
        rss_mb = usage.ru_maxrss / 1024.0

    out = {
        "language": "Python 3.14 (GIL + Threading Lock)",
        "standard": "CPython Bytecode Interpreter",
        "total_ops": TOTAL_OPS,
        "threads": NUM_THREADS,
        "elapsed_ms": round(elapsed_sec * 1000.0, 2),
        "throughput_ops_sec": round(ops_sec),
        "avg_latency_ns": round(avg_latency_ns, 2),
        "total_committed": ring.total_committed,
        "contention_retries": ring.contention_retries,
        "peak_rss_mb": round(rss_mb, 2),
    }

    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
