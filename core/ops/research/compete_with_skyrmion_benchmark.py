import time
import os
import mmap
import ctypes

# Simulating the exact hardware mapping to beat Skyrmion:
# Apple Silicon M4 has 128-byte L1 Cache lines.
# We map our HexCells directly to memory-mapped NVMe storage to simulate non-volatile cache.

FILE_PATH = "hexcell_racetrack.bin"
NUM_CELLS = 1_000_000  # 128 MB
FILE_SIZE = NUM_CELLS * 128

def create_mmap_file():
    with open(FILE_PATH, "wb") as f:
        f.seek(FILE_SIZE - 1)
        f.write(b'\0')

def benchmark_hexcell_racetrack():
    with open(FILE_PATH, "r+b") as f:
        # mmap gives us zero-copy, memory-mapped non-volatile storage
        mm = mmap.mmap(f.fileno(), FILE_SIZE)
        
        start_time = time.perf_counter()
        
        # Simulate moving a pointer across the memory (like a skyrmion racetrack)
        # We read/write the 128-byte cells sequentially to maximize L1 cache prefetching
        # 1,000,000 cells = 128 MB of data
        # In Python, this is slow, so we just do a native byte-array overwrite
        
        # We write 128-byte blocks
        block = b'\xBE\xAF' * 64
        
        # Write loop
        for i in range(0, FILE_SIZE, 128):
            mm[i:i+128] = block
            
        mm.flush()
        end_time = time.perf_counter()
        
        elapsed = end_time - start_time
        throughput_mb = (128) / elapsed
        
        print(f"XORAS HEXCELL RACETRACK (Non-Volatile NVMe mmap):")
        print(f"Time to traverse 1,000,000 cells (128 MB): {elapsed:.6f} seconds")
        print(f"Throughput: {throughput_mb:.2f} MB/s (Python Overhead Limited)")
        
        mm.close()
        
if __name__ == "__main__":
    if not os.path.exists(FILE_PATH):
        create_mmap_file()
    benchmark_hexcell_racetrack()
