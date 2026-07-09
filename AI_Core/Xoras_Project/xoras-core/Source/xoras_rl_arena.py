import sqlite3
import json
import random
import time
import os
from xoras_particle import XorasParticle


class RLArena:
    def __init__(self, db_path="xoras_memory.db"):
        self.db_path = db_path
        self.particles = []
        self.generations = 0

    def _load_historical_ticks(self):
        """Extracts market history from the migrated SQLite WAL."""
        if not os.path.exists(self.db_path):
            return [
                {"bids": [[60000 + i, 1.0]], "asks": [[60001 + i, 1.0]]}
                for i in range(100)
            ]

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT metadata FROM memory_vectors ORDER BY id ASC")
            rows = cursor.fetchall()
            conn.close()

            ticks = []
            for row in rows:
                try:
                    data = json.loads(row[0])
                    if 'market_state' in data:
                        # Normalize to expected input
                        ticks.append({
                            "bids": [[data['market_state'].get('bid', 0), 1.0]],
                            "asks": [[data['market_state'].get('ask', 0), 1.0]]
                        })
                except Exception:
                    continue
            if not ticks:
                return [
                    {"bids": [[60000 + i, 1.0]], "asks": [[60001 + i, 1.0]]}
                    for i in range(100)
                ]
            return ticks
        except Exception as e:
            print(f"[RL-ARENA] Error reading DB: {e}")
            return [{"bids": [[60000, 1.0]], "asks": [[60001, 1.0]]}]

    def spawn_generation(self, count=1000):
        print(f"[RL-ARENA] Spawning Generation {self.generations}: {count} particles.")
        self.particles = []
        for i in range(count):
            p = XorasParticle(particle_id=f"GEN{self.generations}_P{i}")
            # Mutate internal thresholds slightly for RL exploration
            p.volatility_threshold = random.uniform(0.0001, 0.0050)
            p.spread_tolerance = random.uniform(0.1, 5.0)
            p.internal_capital = 10000.0  # $10k starting capital
            self.particles.append(p)

    def run_simulation(self):
        ticks = self._load_historical_ticks()
        print(
            f"[RL-ARENA] Simulating {len(ticks)} "
            "historical micro-events across swarm..."
        )

        start_time = time.perf_counter()
        for tick in ticks:
            # Broadcast to swarm
            for p in self.particles:
                p.ingest_tick(tick)
                # Simulated trade execution logic based on threshold
                spread = float(tick['asks'][0][0]) - float(tick['bids'][0][0])
                if spread > p.spread_tolerance:
                    # Simulated profit
                    p.internal_capital += (spread * 0.5)

        elapsed = time.perf_counter() - start_time
        print(f"[RL-ARENA] Simulation complete in {elapsed:.4f}s.")

    def select_alpha(self):
        if not self.particles:
            return None
        # Sort by highest internal capital
        self.particles.sort(key=lambda x: getattr(
            x, 'internal_capital', 0.0), reverse=True)
        alpha = self.particles[0]
        final_cap = getattr(alpha, 'internal_capital', 0.0)
        print(
            f"[RL-ARENA] ALPHA SELECTED: {alpha.id} | "
            f"Final Capital: ${final_cap:.2f}"
        )
        return alpha

    def export_alpha(self, alpha):
        weights = {
            "volatility_threshold": alpha.volatility_threshold,
            "spread_tolerance": alpha.spread_tolerance
        }
        with open("alpha_weights.json", "w") as f:
            json.dump(weights, f)
        print(
            "[RL-ARENA] Alpha weights serialized to disk "
            "for Swarm Manager injection."
        )


if __name__ == "__main__":
    arena = RLArena(
        db_path=(
            "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/"
            "Source/xoras_memory.db"
        )
    )
    arena.spawn_generation(1000)
    arena.run_simulation()
    alpha = arena.select_alpha()
    if alpha:
        arena.export_alpha(alpha)
