import time
import os
import mmap

FILE_PATH_128 = "scratch/hardware_bins/hexcell_128_test.bin"
FILE_PATH_256 = "scratch/hardware_bins/hexcell_256_test.bin"
NUM_CELLS = 1_000_000

def create_files():
    with open(FILE_PATH_128, "wb") as f:
        f.seek((NUM_CELLS * 128) - 1)
        f.write(b'\0')
    with open(FILE_PATH_256, "wb") as f:
        f.seek((NUM_CELLS * 256) - 1)
        f.write(b'\0')

def benchmark(file_path, cell_size):
    file_size = NUM_CELLS * cell_size
    with open(file_path, "r+b") as f:
        mm = mmap.mmap(f.fileno(), file_size)
        block = b'\xBE\xAF' * (cell_size // 2)
        
        start_time = time.perf_counter()
        for i in range(0, file_size, cell_size):
            mm[i:i+cell_size] = block
        mm.flush()
        elapsed = time.perf_counter() - start_time
        
        throughput_mb = (file_size / (1024*1024)) / elapsed
        print(f"[{cell_size}-BYTE HEXCELL] Time: {elapsed:.4f}s | Throughput: {throughput_mb:.2f} MB/s (Python Limited)")
        mm.close()

if __name__ == "__main__":
    create_files()
    benchmark(FILE_PATH_128, 128)
    benchmark(FILE_PATH_256, 256)
