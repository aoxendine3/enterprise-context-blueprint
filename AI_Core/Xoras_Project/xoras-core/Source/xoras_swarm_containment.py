# --- XORAS SWARM CONTAINMENT & REDIRECTION NODE (XSCRN) ---
# Purpose: High-speed swarm process isolation using Byzantine consensus agreement.
# Classification: [PRODUCTION] / [EMULATED]

import asyncio
import time
from Source.xoras_shm_bft import XorasShmBft

class XorasSwarmContainment:
    def __init__(self, num_agents=148, num_byzantine=49):
        self.num_agents = num_agents
        self.num_byzantine = num_byzantine
        
        # Instantiate SHM-BFT engine to achieve consensus on anomaly isolation
        self.bft_engine = XorasShmBft(
            num_nodes=self.num_agents,
            num_byzantine=self.num_byzantine,
            latency_min_ms=0.0,
            latency_max_ms=0.0
        )
        
        self.active_agents = self._initialize_agents()
        self.isolation_log = []

    def _initialize_agents(self) -> dict:
        agents = {}
        for i in range(self.num_agents):
            agents[i] = {
                "id": i,
                "status": "healthy",
                "cpu_usage": 5.0,
                "latency_ms": 2.0,
                "sandbox_violations": 0
            }
        return agents

    def update_agent_telemetry(self, agent_id: int, metrics: dict):
        """Update telemetry metrics for a specific agent."""
        if agent_id in self.active_agents:
            self.active_agents[agent_id].update(metrics)

    async def audit_and_contain(self, target_agent_id: int) -> dict:
        """
        Audits a target agent. If telemetry indicates a compromise, runs BFT consensus
        across the swarm to isolate the agent. Returns audit details.
        """
        start_time = time.perf_counter()
        
        if target_agent_id not in self.active_agents:
            return {"status": "error", "message": "Target agent not found."}
            
        agent = self.active_agents[target_agent_id]
        
        # Isolation Trigger Check (e.g. sandbox breach or extreme latency)
        needs_isolation = (agent["sandbox_violations"] > 0) or (agent["latency_ms"] >= 500.0)
        
        consensus_reached = False
        final_value = False
        bft_metrics = {}
        
        if needs_isolation:
            # Run high-speed BFT consensus round across the remaining 147 nodes to agree on isolation
            bft_metrics = await self.bft_engine.run_consensus_round(proposal_value=True)
            consensus_reached = bft_metrics["consensus_reached"]
            final_value = bft_metrics["final_value"]
            
            if consensus_reached and final_value:
                # Isolate and freeze the target process
                agent["status"] = "isolated"
                self.isolation_log.append({
                    "agent_id": target_agent_id,
                    "reason": "Consensus-backed isolation triggered",
                    "timestamp": time.time()
                })
                
        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000.0
        
        return {
            "target_id": target_agent_id,
            "isolation_triggered": needs_isolation,
            "isolation_committed": consensus_reached and final_value,
            "target_status": agent["status"],
            "bft_metrics": bft_metrics,
            "elapsed_ms": elapsed_ms
        }

    def cleanup(self):
        """Free and unlink the underlying SHM-BFT OS shared memory segment."""
        self.bft_engine.cleanup()
