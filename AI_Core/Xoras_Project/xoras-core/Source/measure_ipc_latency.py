import subprocess
import time
import os


def measure():
    engine_path = "./xoras_hft_engine"
    cwd = os.path.dirname(os.path.abspath(__file__))

    # Check if binary exists
    if not os.path.exists(os.path.join(cwd, engine_path)):
        print(f"Error: {engine_path} not found in {cwd}")
        return

    # Start the C++ engine
    proc = subprocess.Popen(
        [engine_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd
    )

    # Read boot lines (2 lines)
    proc.stdout.readline()
    proc.stdout.readline()

    # A valid 17-token line representing order book depth
    payload = "BTCUSDT,6500000,1000,6499900,900,6499800,800,6499700,700,6500100,1000,6500200,900,6500300,800,6500400,700\n"

    latencies = []

    # Run 100 trials to get a clean average
    for _ in range(100):
        start = time.perf_counter()
        proc.stdin.write(payload.encode())
        proc.stdin.flush()

        line = proc.stdout.readline()
        end = time.perf_counter()

        # Latency in microseconds
        latency_us = (end - start) * 1_000_000
        latencies.append(latency_us)

    proc.terminate()
    proc.wait()

    avg_latency = sum(latencies) / len(latencies)
    min_latency = min(latencies)
    max_latency = max(latencies)

    print(f"--- IPC PIPE OVERHEAD RESULTS (100 trials) ---")
    print(f"Average Round-Trip Latency: {avg_latency:.2f} us")
    print(f"Minimum Latency: {min_latency:.2f} us")
    print(f"Maximum Latency: {max_latency:.2f} us")


if __name__ == "__main__":
    measure()
