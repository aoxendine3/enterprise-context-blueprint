import asyncio, random, json, time
import redis

class TelemetryGenerator:
    """Continuously produce synthetic telemetry events and push them to a Redis stream.
    Each event contains CPU usage, latency, device identifier, location and an error code.
    """
    def __init__(self, redis_url: str = "redis://localhost:6379/0", stream_name: str = "telemetry"):
        self._redis = redis.from_url(redis_url)
        self._stream = stream_name

    async def generate(self) -> None:
        """Generate events forever. The sleep interval is random to simulate bursty traffic."""
        while True:
            event = {
                "timestamp": time.time(),
                "cpu": random.uniform(0, 100),
                "latency_ms": random.uniform(0, 1000),
                "device_id": f"dev-{random.randint(1, 1000)}",
                "location": random.choice(["us-east", "us-west", "eu-central", "ap-south"]),
                "error_code": random.choice([0, 1, 2, 3, 4, 5]),
            }
            # Redis expects mapping of bytes; conversion handled by redis-py automatically for dicts with simple types.
            self._redis.xadd(self._stream, event)
            # Random short pause (10‑100 ms) to create spikes.
            await asyncio.sleep(random.uniform(0.01, 0.1))
