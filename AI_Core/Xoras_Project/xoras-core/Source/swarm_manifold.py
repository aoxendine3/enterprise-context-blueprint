import asyncio
import time
import psutil
from xoras_particle import XorasParticle


class SwarmManifold:
    """
    The central orchestration engine for the Xoras Swarm.
    Dynamically scales and coordinates thousands of XorasParticles.
    """

    def __init__(self, db_path="/Users/ajoxendine68/Desktop/Xoras_Project/Omni_Dojo_Sandbox/manifold.db"):
        self.particles = []
        self.db_path = db_path
        self.is_active = False

    def check_system_resources(self):
        """
        Calculates safe maximums based on available RAM and CPU.
        Returns a suggested maximum particle count to prevent OS freezes.
        """
        mem = psutil.virtual_memory()
        cpu_count = psutil.cpu_count(logical=True)
        # Very rough estimate: assume each particle requires ~1MB overhead in asyncio
        available_mb = mem.available / (1024 * 1024)
        # e.g. 1000 per logical core max
        safe_max = int(min(available_mb * 0.8, cpu_count * 1000))
        return safe_max

    def spawn_particles(self, count, rank="Drone", ignore_limits=False):
        safe_max = self.check_system_resources()
        print(f"[MANIFOLD] Hardware check: Safe maximum is {safe_max} particles.")

        if count > safe_max and not ignore_limits:
            print(
                f"[WARNING] Requested {count} exceeds safe max {safe_max}. Throttling to safe maximum.")
            count = safe_max
        elif count > safe_max and ignore_limits:
            print(
                f"[DANGER] Override active. Spawning {count} particles despite hardware warnings.")

        print(f"[MANIFOLD] Spawning {count} [{rank}] particles...")
        start = time.time()
        new_particles = [XorasParticle(rank=rank) for _ in range(count)]
        self.particles.extend(new_particles)

        print(
            f"[MANIFOLD] Spawned {len(new_particles)} particles in {time.time() - start:.4f} seconds.")
        return new_particles

    async def execute_topology(self, tasks):
        """
        Distributes a list of tasks across all active particles dynamically.
        """
        if not self.particles:
            print("[MANIFOLD] No particles spawned. Topology execution aborted.")
            return

        self.is_active = True
        print(
            f"[MANIFOLD] Initiating Vectorized Execution of {len(tasks)} tasks across {len(self.particles)} particles...")

        start_time = time.time()

        # Simple round-robin distribution
        coroutines = []
        for i, task in enumerate(tasks):
            assigned_particle = self.particles[i % len(self.particles)]
            coroutines.append(assigned_particle.execute_task(task))

        # Execute concurrently
        results = await asyncio.gather(*coroutines)

        end_time = time.time()
        self.is_active = False

        print(f"\n[MANIFOLD] Topology Collapse Complete.")
        print(f"-> Time elapsed: {end_time - start_time:.4f} seconds")
        print(f"-> Tasks processed: {len(results)}")

        return results


async def test_swarm():
    print("=== XORAS SWARM MANIFOLD: STRESS TEST ===")
    manifold = SwarmManifold()

    # Spawn 100 particles
    manifold.spawn_particles(100, rank="Auditor")

    # Generate 1000 synthetic tasks
    synthetic_tasks = [f"TopologyNode_{i}" for i in range(1000)]

    # Execute the topology
    await manifold.execute_topology(synthetic_tasks)

if __name__ == "__main__":
    asyncio.run(test_swarm())
