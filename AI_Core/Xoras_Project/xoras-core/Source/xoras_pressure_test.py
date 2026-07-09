#!/usr/bin/env python3.12
"""
Universal Pressure Test for Xoras Core System
Designed to test concurrency limits and API throughput while monitoring memory usage.
"""

import asyncio
import time
import psutil
import json
import urllib.request
import urllib.error

# Config
OLLAMA_URL = "http://192.168.1.133:11434/api/generate"
TEST_MODEL = "qwen2.5-coder:1.5b"
CONCURRENCY = 10


def check_memory():
    vm = psutil.virtual_memory()
    print(
        f"[METRIC] CPU: {psutil.cpu_percent()}% | Free RAM: {vm.available / (1024*1024):.2f} MB")
    return vm.available


async def simulate_websocket_stream(task_id: int):
    """Simulates incoming tick data over a websocket."""
    start_time = time.time()
    for i in range(50):
        # Simulate processing delay
        await asyncio.sleep(0.01)
    duration = time.time() - start_time
    print(f"[TASK {task_id}] Completed 50 stream cycles in {duration:.3f}s")


def ping_llm():
    """Pings the local Ollama backend to test response latency."""
    data = json.dumps({
        "model": TEST_MODEL,
        "prompt": "Respond with 'ACK'.",
        "stream": False
    }).encode("utf-8")

    req = urllib.request.Request(OLLAMA_URL, data=data, headers={
                                 "Content-Type": "application/json"})
    start_time = time.time()
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode())
            latency = time.time() - start_time
            print(
                f"[LLM] Success. Latency: {latency:.3f}s. Response: {result.get('response', '').strip()}")
            return True
    except Exception as e:
        latency = time.time() - start_time
        print(f"[LLM] Failed. Latency: {latency:.3f}s. Error: {e}")
        return False


async def main():
    print("=== XORAS UNIVERSAL PRESSURE TEST ===")
    check_memory()

    print("\n--- Phase 1: LLM Endpoint Test ---")
    ping_llm()

    print(f"\n--- Phase 2: Asynchronous Concurrency Test ({CONCURRENCY} Tasks) ---")
    tasks = [simulate_websocket_stream(i) for i in range(CONCURRENCY)]
    await asyncio.gather(*tasks)

    print("\n--- Phase 3: Post-Test Memory Check ---")
    free_mem = check_memory()

    if free_mem < 50 * 1024 * 1024:
        print("[WARNING] SYSTEM AT CRITICAL MEMORY PRESSURE (<50MB FREE)")
    else:
        print("[OK] System memory is stable after load.")

    print("=== TEST COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(main())
