#!/Users/ajoxendine68/sovereign/.venv/bin/python3.12
import asyncio
import threading
import time
import os
import sys
import subprocess
from xoras_sovereign_ai import SovereignBrain
from xoras_arbitrage_engine import ArbitrageEngine
from xoras_swarm_manager import XorasSwarmManager
import sentinel_core # Re-using our OPSEC module

class OmniCore:
    def __init__(self):
        self.brain = SovereignBrain()
        self.arbitrage = ArbitrageEngine(self.brain)
        self.swarm = XorasSwarmManager()
        self.sentinel_process = None
        self.signal_process = None

    def _boot_sentinel(self):
        print("[OMNI-CORE] Initiating boot sequence...")
        time.sleep(1)

        print("[OMNI-CORE] Booting Offensive Sentinel (Phase 5)...")
        self.sentinel_process = subprocess.Popen([sys.executable, "xoras_sentinel_offensive.py"])
        time.sleep(2) # Give Sentinel time to arm the perimeter

        print("[OMNI-CORE] Booting MT5 Signal Provider Daemon (Background)...")
        self.signal_process = subprocess.Popen([sys.executable, "xoras_signal_provider.py"])
        time.sleep(1)

        print("[OMNI-CORE] Booting Sub-Systems...")
        sentinel_core.init_db()
        monitor_thread = threading.Thread(target=sentinel_core.monitor_network, daemon=True)
        monitor_thread.start()
        server_thread = threading.Thread(target=sentinel_core.run_server, args=(9090,), daemon=True)
        server_thread.start()
        print("[OMNI-CORE] Sentinel Online. Weaponized Perimeter Active.\n")

    async def _consciousness_heartbeat(self):
        print("[CONSCIOUSNESS] Autonomous heartbeat online.")
        while True:
            await asyncio.sleep(6) # Beat every 6 seconds to manage thermals
            system_state = {
                "active_trades": self.arbitrage.active_trades,
                "ai_decisions": self.brain.total_decisions,
                "volume": f"${self.arbitrage.total_volume:.2f}"
            }
            thought = await self.brain.generate_internal_thought(system_state)
            print(f"\n[XORAS-INTERNAL]: {thought}")

    async def _daemon_supervisor(self):
        """Asynchronously monitors Sentinel, MT5, databases, and Ollama using the SelfHealingManager."""
        from xoras_self_healing import SelfHealingManager
        healing = SelfHealingManager()
        print("[SUPERVISOR] Self-healing daemon monitoring heartbeat active.")
        
        while True:
            await asyncio.sleep(4) # Check health every 4 seconds
            
            # 1. Register or update active PIDs
            if self.sentinel_process:
                healing.register_process("OffensiveSentinel", self.sentinel_process.pid)
            if self.signal_process:
                healing.register_process("MT5SignalProvider", self.signal_process.pid)
            if self.arbitrage.hft_process:
                healing.register_process("HFTEngine", self.arbitrage.hft_process.pid)
                
            # 2. Check Database Integrity
            await healing.check_database_integrity()
            
            # 3. Check Ollama Health
            await healing.check_ollama_health()
            
            # 4. Monitor Process Resource Usage (leak and runaway protection)
            actions = await healing.monitor_resources()
            
            # 5. Execute restarts if requested
            if "OffensiveSentinel" in actions:
                print("\n[ALERT] [SELF-HEALING] Restarting Offensive Sentinel...")
                if self.sentinel_process:
                    try:
                        self.sentinel_process.kill()
                    except Exception:
                        pass
                self.sentinel_process = subprocess.Popen([sys.executable, "xoras_sentinel_offensive.py"])
                
            if "MT5SignalProvider" in actions:
                print("\n[ALERT] [SELF-HEALING] Restarting MT5 Signal Provider...")
                if self.signal_process:
                    try:
                        self.signal_process.kill()
                    except Exception:
                        pass
                self.signal_process = subprocess.Popen([sys.executable, "xoras_signal_provider.py"])

            if "HFTEngine" in actions:
                print("\n[ALERT] [SELF-HEALING] Restarting C++ HFT Engine...")
                await self.arbitrage.stop_hft_engine()
                await self.arbitrage.start_hft_engine()

    async def _boot_engines(self):
        print("\n[OMNI-CORE] Initializing Sovereign AI Link...")
        await self.brain.check_health()
        
        print("\n[OMNI-CORE] Launching Arbitrage Engine (C++ Event Loop)...")
        # Run for 20 seconds to demonstrate the power without leaving a permanent process hanging
        engine_task = asyncio.create_task(self.arbitrage.ignite_streams())
        heartbeat_task = asyncio.create_task(self._consciousness_heartbeat())
        supervisor_task = asyncio.create_task(self._daemon_supervisor())
        
        await asyncio.sleep(20)
        
        print("\n[OMNI-CORE] Burn Complete. Shutting down active websockets and heartbeat.")
        engine_task.cancel()
        heartbeat_task.cancel()
        supervisor_task.cancel()
        
        try:
            await engine_task
            await heartbeat_task
            await supervisor_task
        except asyncio.CancelledError:
            pass

    def _boot_background_services(self):
        """Start persona API and dream orchestrator as background daemons."""
        source_dir = os.path.dirname(os.path.abspath(__file__))

        def _run_persona_api():
            try:
                subprocess.Popen(
                    [sys.executable, "xoras_persona_api.py"],
                    cwd=source_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                print("[OMNI-CORE] Persona API sidecar starting on :8787")
            except Exception as e:
                print(f"[OMNI-CORE] Persona API boot failed: {e}")

        def _run_dream_orchestrator():
            try:
                subprocess.Popen(
                    [sys.executable, "xoras_dream_orchestrator.py"],
                    cwd=source_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                print("[OMNI-CORE] Dream orchestrator daemon starting")
            except Exception as e:
                print(f"[OMNI-CORE] Dream orchestrator boot failed: {e}")

        threading.Thread(target=_run_persona_api, daemon=True).start()
        threading.Thread(target=_run_dream_orchestrator, daemon=True).start()

    def execute(self):
        print("==========================================")
        print("         XORAS OMNI-SYSTEM CORE           ")
        print("==========================================\n")
        try:
            self._boot_sentinel()
            self._boot_background_services()
            
            # Test Swarm Architecture
            print("\n[OMNI-CORE] Booting Xoras Swarm Architecture...")
            profiles = [
                self.swarm.define_agent_profile("QuantumNode-1", "Forex Arbitrage Parallel Agent"),
                self.swarm.define_agent_profile("SecNode-2", "Codebase Vulnerability Researcher")
            ]
            tasks = [
                "Process live ticks for EUR/JPY and USD/CHF",
                "Hunt for logic flaws in latest GitHub commits"
            ]
            asyncio.run(self.swarm.invoke_swarm(profiles, tasks))
            
            # Start async high-frequency operations
            asyncio.run(self._boot_engines())
        finally:
            print("\n[OMNI-CORE] Disarming network perimeter and signal providers...")
            if self.sentinel_process:
                self.sentinel_process.terminate()
                self.sentinel_process.wait()
            if self.signal_process:
                self.signal_process.terminate()
                self.signal_process.wait()
            
            print("\n==========================================")
            print("           OMNI-SYSTEM OFFLINE            ")
            print("==========================================")
            print(f"Total AI Decisions : {self.brain.total_decisions}")
            print(f"Total Trades Exec  : {self.arbitrage.active_trades}")
            print(f"Total Volume Flow  : ${self.arbitrage.total_volume:.2f}")
            print("==========================================\n")

if __name__ == "__main__":
    omni = OmniCore()
    omni.execute()
