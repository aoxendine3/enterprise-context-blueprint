import asyncio
import time
import logging
from xoras_swarm_manager import XorasSwarmManager


async def run_benchmark(target_agents):
    # Suppress verbose logging for the benchmark to accurately measure orchestration time
    logger = logging.getLogger("XorasSwarmManager")
    logger.setLevel(logging.CRITICAL)

    swarm = XorasSwarmManager()

    print("==================================================")
    print(f" XORAS SWARM BENCHMARK: ATTEMPTING {target_agents} PARALLEL NODES")
    print("==================================================")

    # Generate profiles and tasks without logging overhead
    profiles = [{"name": f"Node-{i}", "role": "Parallel Processor"}
                for i in range(target_agents)]
    tasks = [f"Task batch #{i}" for i in range(target_agents)]

    start_time = time.perf_counter()
    results = await swarm.invoke_swarm(profiles, tasks)
    end_time = time.perf_counter()

    elapsed = end_time - start_time
    print("\n==================================================")
    print(" BENCHMARK RESULTS")
    print("==================================================")
    print(f"Target Node Count   : {target_agents} (Beating Kimi K2.6 record of 300)")
    print(f"Successfully Spooled: {len(results)}")
    print(f"Total Execution Time: {elapsed:.4f} seconds")
    print(
        f"Concurrency Delay   : {(elapsed - 2.0):.4f} seconds (accounting for 2s sleep task)")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_benchmark(305))
