import subprocess
import time
import os
import struct
import multiprocessing.shared_memory as shm


def run_pipe_bench():
    engine_path = "./xoras_hft_engine"
    cwd = os.path.dirname(os.path.abspath(__file__))

    proc = subprocess.Popen(
        [engine_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        cwd=cwd
    )
    # Read boot lines
    proc.stdout.readline()
    proc.stdout.readline()

    payload = "BTCUSDT,6500000,1000,6499900,900,6499800,800,6499700,700,6500100,1000,6500200,900,6500300,800,6500400,700\n"

    latencies = []
    for _ in range(1000):
        start = time.perf_counter()
        proc.stdin.write(payload.encode())
        proc.stdin.flush()
        line = proc.stdout.readline()
        end = time.perf_counter()
        latencies.append((end - start) * 1_000_000)

    proc.terminate()
    proc.wait()
    return latencies


def run_shm_bench():
    engine_path = "./xoras_hft_shm_engine"
    cwd = os.path.dirname(os.path.abspath(__file__))

    # Attempt to create segment. If it exists, force unlink and recreate.
    try:
        segment = shm.SharedMemory(name="xoras_shm_ring", create=True, size=8320)
    except FileExistsError:
        stale = shm.SharedMemory(name="xoras_shm_ring", create=False)
        stale.close()
        stale.unlink()
        segment = shm.SharedMemory(name="xoras_shm_ring", create=True, size=8320)

    struct.pack_into("QQQQ", segment.buf, 0, 0, 0, 0, 0)

    proc = subprocess.Popen(
        [engine_path],
        stdout=subprocess.DEVNULL,  # Redirect to DEVNULL to prevent print Deadlocks
        stderr=subprocess.DEVNULL,
        cwd=cwd
    )
    time.sleep(0.1)  # Wait for engine to initialize

    payload = "BTCUSDT,6500000,1000,6499900,900,6499800,800,6499700,700,6500100,1000,6500200,900,6500300,800,6500400,700"

    latencies = []
    for i in range(1000):
        start = time.perf_counter()

        # Write to input slot
        head = struct.unpack_from("Q", segment.buf, 0)[0]
        slot_idx = head % 16
        slot_offset = 128 + slot_idx * 256
        encoded = payload.encode('utf-8') + b'\x00'
        segment.buf[slot_offset: slot_offset + len(encoded)] = encoded
        struct.pack_into("Q", segment.buf, 0, head + 1)

        # Poll output_head (offset 16)
        while True:
            out_head = struct.unpack_from("Q", segment.buf, 16)[0]
            if out_head > head:
                # Read response slot for parity
                slot_offset_out = 4224 + slot_idx * 256
                resp = segment.buf[slot_offset_out: slot_offset_out + 256].tobytes()

                # Advance output_tail
                struct.pack_into("Q", segment.buf, 24, head + 1)
                break
            time.sleep(0)  # Yield CPU core to C++ process to prevent core starvation

        end = time.perf_counter()
        latencies.append((end - start) * 1_000_000)

    proc.terminate()
    proc.wait()
    segment.close()
    segment.unlink()
    return latencies


def main():
    print("Starting side-by-side IPC latency benchmark (1000 trials each)...")
    print("Running Pipe-based benchmark...")
    pipe_lats = run_pipe_bench()

    print("Running Shared-Memory-based benchmark...")
    shm_lats = run_shm_bench()

    # Calculate stats
    pipe_avg = sum(pipe_lats) / len(pipe_lats)
    pipe_min = min(pipe_lats)
    pipe_max = max(pipe_lats)

    shm_avg = sum(shm_lats) / len(shm_lats)
    shm_min = min(shm_lats)
    shm_max = max(shm_lats)

    speedup = pipe_avg / shm_avg

    print("\n--- IPC BENCHMARK RESULTS ---")
    print(
        f"PIPE LATENCY: Avg={pipe_avg:.2f} us | Min={pipe_min:.2f} us | Max={pipe_max:.2f} us")
    print(
        f"SHM LATENCY:  Avg={shm_avg:.2f} us | Min={shm_min:.2f} us | Max={shm_max:.2f} us")
    print(f"IPC Speedup Factor: {speedup:.2f}x faster")


if __name__ == "__main__":
    main()
