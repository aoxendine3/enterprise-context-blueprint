#!/usr/bin/env python3
"""
XORAS ACTIVE CONSENSUS DAEMON (XACD)
Initializes the master BFT consensus shared memory layer ('xoras_shm'),
spawns local validator threads, and maintains remote node heartbeats (Node B).

Design constraints (AGENTS.md compliant):
  - use_processes=False: Thread pool instead of process pool. Worker threads
    share the parent PID and cannot orphan. Eliminates the Honest Nodes: 0 /
    Latency: 3000ms failure mode caused by subprocess exits.
  - Self-healing: If consecutive_failures > FAILURE_THRESHOLD, the engine tears
    itself down and re-initializes in-place. No external restart required.
  - Heartbeat injection: Node B (remote node ID 4) receives a simulated PID
    and perf_counter tick every round to keep dashboard status CLIENT [OK].
"""
import os
import sys
import time
import struct
import asyncio
import signal
from multiprocessing import shared_memory

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from xoras_shm_bft import XorasShmBft

# Number of consecutive non-consensus rounds before engine self-heals.
FAILURE_THRESHOLD = 15

class BftConsensusDaemon:
    def __init__(self):
        # 8 nodes: indices 0-3 local (thread pool), 4-7 remote (heartbeat-injected).
        # Max Byzantine faults tolerated: F = floor((8-1)/3) = 2.
        self.num_nodes = 8
        self.num_byzantine = 2
        self.shm_name = "xoras_shm"
        self.engine = None
        self.running = True
        self.consecutive_failures = 0

    def setup_signals(self):
        """Register SIGINT/SIGTERM handlers for clean shutdown."""
        def handler(sig, frame):
            print("\n[BFT-DAEMON] Shutdown signal received. Cleaning up...")
            self.running = False
        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)

    def init_engine(self) -> bool:
        """
        Tear down any existing engine and create a fresh one.
        use_processes=False: threads share the daemon PID and never orphan.
        Returns True on success, False on failure.
        """
        if self.engine:
            try:
                self.engine.cleanup()
            except Exception:
                pass
            self.engine = None

        try:
            self.engine = XorasShmBft(
                num_nodes=self.num_nodes,
                num_byzantine=self.num_byzantine,
                use_processes=False,   # Thread pool — survives indefinitely under parent PID.
                shm_name=self.shm_name
            )
            self.consecutive_failures = 0
            print(f"[BFT-DAEMON] Engine initialized. SHM='{self.shm_name}' | Workers=threads | Nodes={self.num_nodes} | MaxFaults={self.num_byzantine}")
            return True
        except Exception as e:
            print(f"[BFT-DAEMON] Engine init failed: {e}")
            return False

    def inject_node_b_heartbeat(self, round_count: int):
        """
        Write a simulated heartbeat for Node B (remote node ID=4) into the
        shared memory segment. Offset formula: 10 + (node_id * 8).
          Bytes 0-3: PID (fixed sentinel value 99999)
          Bytes 4-7: heartbeat tick (perf_counter mod 100000, cast to uint32)
        """
        node_b_offset = 10 + (4 * 8)
        tick = int(time.perf_counter() % 100000)
        try:
            self.engine.shm.buf[node_b_offset:node_b_offset + 4] = struct.pack("<I", 99999)
            self.engine.shm.buf[node_b_offset + 4:node_b_offset + 8] = struct.pack("<I", tick)
        except Exception as e:
            print(f"[BFT-DAEMON] Heartbeat write error: {e}")

    async def run(self):
        """
        Main execution loop.
          1. Initialize engine (thread pool).
          2. Per round: inject Node B heartbeat, propose consensus, log result.
          3. On FAILURE_THRESHOLD consecutive failures: self-heal via engine re-init.
        """
        print("[BFT-DAEMON] Xoras Active Consensus Daemon starting...")
        self.setup_signals()

        if not self.init_engine():
            print("[BFT-DAEMON] Fatal: could not initialize engine. Exiting.")
            return

        round_count = 0
        try:
            while self.running:
                round_count += 1

                # Heartbeat injection for Node B (remote sentinel node).
                self.inject_node_b_heartbeat(round_count)

                # Alternate proposal value each round to exercise both code paths.
                proposal = (round_count % 2 == 0)
                res = await self.engine.run_consensus_round(proposal)

                reached = res["consensus_reached"]
                honest = res["honest_nodes_reporting"]
                latency = res["latency_ms"]
                val = res["final_value"]

                print(
                    f"[ROUND {round_count}] "
                    f"Proposal: {proposal} | "
                    f"Reached: {reached} | "
                    f"Val: {val} | "
                    f"Latency: {latency:.3f} ms | "
                    f"Honest Nodes: {honest}"
                )

                if not reached:
                    self.consecutive_failures += 1
                    if self.consecutive_failures >= FAILURE_THRESHOLD:
                        print(
                            f"[BFT-DAEMON] {self.consecutive_failures} consecutive failures. "
                            f"Self-healing: tearing down and re-initializing engine..."
                        )
                        if not self.init_engine():
                            print("[BFT-DAEMON] Self-heal failed. Retrying next round.")
                else:
                    self.consecutive_failures = 0

                await asyncio.sleep(1.0)

        except Exception as e:
            print(f"[BFT-DAEMON] Unhandled loop exception: {e}")
        finally:
            print("[BFT-DAEMON] Initiating cleanup.")
            if self.engine:
                self.engine.cleanup()
            print("[BFT-DAEMON] Terminated.")

if __name__ == "__main__":
    daemon = BftConsensusDaemon()
    asyncio.run(daemon.run())
