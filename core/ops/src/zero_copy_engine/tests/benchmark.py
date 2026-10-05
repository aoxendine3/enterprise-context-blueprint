import time
import ctypes
import os

NUM_CELLS = 500_000
CELL_SIZE = 3200
BUFFER_SIZE = NUM_CELLS * CELL_SIZE
GB_SIZE = BUFFER_SIZE / (1024**3)

buffer = bytearray(BUFFER_SIZE)
for i in range(NUM_CELLS):
    buffer[i * CELL_SIZE + 3168] = (i % 255)

start_time = time.time()
checksum = 0
for i in range(NUM_CELLS):
    checksum = (checksum + buffer[i * CELL_SIZE + 3168])
    if checksum >= 2**31 - 1:
        checksum = 0
py_time = time.time() - start_time
py_throughput = GB_SIZE / py_time

lib_path = "./target/release/libzero_copy_engine.dylib"
lib = ctypes.CDLL(lib_path)
lib.process_batch_zero_copy.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
lib.process_batch_zero_copy.restype = ctypes.c_int32

c_buffer = (ctypes.c_char * BUFFER_SIZE).from_buffer(buffer)

start_time = time.time()
rust_checksum = lib.process_batch_zero_copy(c_buffer, NUM_CELLS)
rust_time = time.time() - start_time
rust_throughput = GB_SIZE / rust_time

print(f"Memory: {GB_SIZE:.6f} GB")
print(f"Python Time: {py_time:.6f} s | Throughput: {py_throughput:.2f} GB/s")
print(f"Rust Time: {rust_time:.6f} s | Throughput: {rust_throughput:.2f} GB/s")
print(f"Speedup: {py_time/rust_time:.2f}x")
