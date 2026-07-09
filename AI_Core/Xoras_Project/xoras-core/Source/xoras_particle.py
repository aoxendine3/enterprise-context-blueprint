import asyncio
import uuid
import random
import time


class XorasParticle:
    """
    A lightweight, highly concurrent subagent (particle) in the Xoras System.
    """

    def __init__(self, rank="Scout", particle_id=None):
        self.id = particle_id if particle_id else str(uuid.uuid4())[:8]
        self.rank = rank
        self.status = "INITIALIZING"
        self.work_completed = 0
        self.birth_time = time.time()

        # RL Weights
        self.volatility_threshold = 0.001
        self.spread_tolerance = 1.0
        self.internal_capital = 0.0

    def ingest_tick(self, tick):
        """Simulates processing a market tick for RL execution."""
        self.work_completed += 1
        pass

    async def execute_task(self, task_payload):
        """
        Asynchronously executes a task payload.
        """
        self.status = "EXECUTING"
        # Simulate processing time based on task complexity
        processing_time = random.uniform(0.01, 0.1)
        await asyncio.sleep(processing_time)

        self.work_completed += 1
        self.status = "IDLE"

        return {
            "particle_id": self.id,
            "rank": self.rank,
            "result": f"Processed {task_payload}",
            "time_taken": processing_time
        }

    def get_metrics(self):
        return {
            "id": self.id,
            "rank": self.rank,
            "tasks_done": self.work_completed,
            "uptime": time.time() - self.birth_time
        }
