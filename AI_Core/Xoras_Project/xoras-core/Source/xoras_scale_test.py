import asyncio
import time
import psutil
from swarm_manifold import SwarmManifold


async def main():
    manifold = SwarmManifold()
    safe_max = manifold.check_system_resources()

    print(
        f"System Check: Safe limit is {safe_max} particles based on available RAM and CPU.")

    # Let's spawn the safe maximum number of particles
    particles = manifold.spawn_particles(safe_max, rank="Scout")

    # We will process 10,000 tasks
    task_count = 10000
    tasks = [f"Data_Stream_Chunk_{i}" for i in range(task_count)]

    print(
        f"Starting execution of {task_count} tasks across {len(particles)} particles...")

    start_time = time.time()
    mem_before = psutil.virtual_memory().used / (1024 * 1024)

    results = await manifold.execute_topology(tasks)

    duration = time.time() - start_time
    mem_after = psutil.virtual_memory().used / (1024 * 1024)

    print("\n--- Scale Test Results ---")
    print(f"Total Particles Spawned: {len(particles)}")
    print(f"Tasks Completed: {len(results)}")
    print(f"Total Time taken: {duration:.4f} seconds")
    print(f"Throughput: {len(results)/duration:.2f} tasks per second")
    print(f"RAM overhead: {mem_after - mem_before:.2f} MB")
    print("--------------------------")

if __name__ == "__main__":
    asyncio.run(main())
