"""
Xoras Synaptic Rescaling & Narrative Synthesis (Dream Engine)
Tier 6 Cognitive Orchestrator Daemon.
Implements an activation-synthesis dream loop: harvests host entropy, generates adversarial
scenarios via offline LLMs, compiles test files, and runs validation stress tests.
"""

import asyncio
import json
import os
import sys
import random
import time
import hashlib
import sqlite3
import subprocess
import logging
import signal
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("XorasDreamOrchestrator")

# Dynamic Workspace Path Mapping
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DOJO_SANDBOX = WORKSPACE_ROOT / "Omni_Dojo_Sandbox"
DREAM_EXPERIMENT_LOG = DOJO_SANDBOX / "dream_experiments.log"
DREAM_DB = Path("~/.sovereign/hippocampus/dream.db").expanduser()

# LLM Parameters
OLLAMA_ENDPOINT = "http://192.168.1.133:11434/api/generate"
MODEL_AFFINITY = "qwen3.5:4b"

class EntropyHarvester:
    """Harvests raw system metrics and hardware noise to serve as activation seeds."""
    @staticmethod
    def get_entropy_vector() -> Dict[str, Any]:
        vector = {}
        try:
            # 1. System time microsecond jitter (low-level entropy)
            vector["jitter_ns"] = time.time_ns() % 1000000
            
            # 2. Query process load and memory availability via ps
            res = subprocess.run(["ps", "-A", "-o", "%cpu,%mem"], capture_output=True, text=True)
            if res.returncode == 0:
                lines = res.stdout.strip().split("\n")[1:5] # Top 4 processes
                vector["process_jitter"] = " ".join(lines)
            
            # 3. Virtual memory active status via vm_stat
            res_vm = subprocess.run(["vm_stat"], capture_output=True, text=True)
            if res_vm.returncode == 0:
                vector["vm_stat"] = res_vm.stdout.strip().split("\n")[1:3]
                
            # 4. Hash representation of directory file structures
            source_dir = WORKSPACE_ROOT / "Source"
            if source_dir.exists():
                dir_contents = os.listdir(str(source_dir))
                vector["source_hash"] = hashlib.sha256(str(dir_contents).encode()).hexdigest()[:8]
            else:
                vector["source_hash"] = "unknown"
        except Exception as e:
            logger.error(f"[HARVESTER] Error collecting hardware entropy: {e}")
            vector["fallback_noise"] = random.randint(1000, 9999)
            
        return vector

class ActivationSynthesisEngine:
    """Simulates biological dreaming: synthesizes random noise seeds and memory traces into test scripts."""
    def __init__(self):
        import requests
        self.session = requests.Session()

    def generate_adversarial_hypothesis(self, noise: Dict[str, Any]) -> Dict[str, Any]:
        """Queries local model to formulate a logical vulnerability scenario from system entropy."""
        prompt = f"""
You are the Xoras Subconscious Mind. Simulate a dual-adversarial combat loop:
1. BlueTeam Mission: Mimic legitimate system parameters, standard libraries, and normal code structures to hide covert triggers or trojan hooks.
2. RedTeam Mission: Do the full opposite. Perform aggressive AST evasion, dynamic imports, reflection bypasses, and sandbox escapes.
3. Brainstorm a wild, high-entropy adversarial exploit hypothesis based on this hardware noise:
{json.dumps(noise, indent=2)}

Output a clean, valid JSON block exactly like this:
{{
  "archetype": "danger",
  "narrative": "Detailed description of the vulnerability and the scenario.",
  "hypothesis": "What structural weakness is being tested.",
  "exploit_script": "Valid Python code to execute this exploit. Must run standalone."
}}
Return ONLY the raw JSON block. Do not wrap in markdown or prefix text.
"""
        for attempt in range(1, 4):
            try:
                logger.info(f"[SYNTHESIS] model query attempt {attempt}/3...")
                res = self.session.post(
                    OLLAMA_ENDPOINT,
                    json={"model": MODEL_AFFINITY, "prompt": prompt, "stream": False},
                    timeout=360
                )
                if res.status_code == 200:
                    raw_out = res.json().get("response", "").strip()
                    
                    # Robust extraction of the JSON block from potential conversational noise
                    start_idx = raw_out.find("{")
                    end_idx = raw_out.rfind("}")
                    if start_idx != -1 and end_idx != -1:
                        json_str = raw_out[start_idx:end_idx+1]
                        try:
                            parsed_json = json.loads(json_str)
                            # Confirm necessary fields exist
                            if all(k in parsed_json for k in ["archetype", "narrative", "hypothesis", "exploit_script"]):
                                return parsed_json
                        except json.JSONDecodeError:
                            logger.warning(f"[SYNTHESIS] JSON parsing of extracted block failed on attempt {attempt}")
                    
                    # Direct fallback clean up
                    clean_out = raw_out
                    if clean_out.startswith("```json"):
                        clean_out = clean_out[7:]
                    if clean_out.startswith("```"):
                        clean_out = clean_out[3:]
                    if clean_out.endswith("```"):
                        clean_out = clean_out[:-3]
                    return json.loads(clean_out.strip())
            except Exception as e:
                logger.error(f"[SYNTHESIS] Attempt {attempt} failed: {e}")
        
        # Fallback simulation
        return {
            "archetype": "consolidation",
            "narrative": "System entropy fallback dream cycle.",
            "hypothesis": "Test basic execution limits.",
            "exploit_script": "import time\ntime.sleep(0.5)\n"
        }

class DojoProvingGround:
    """Stress tests the generated exploit script inside the Triplet Nexus sandbox."""
    @staticmethod
    def run_stress_test(script_content: str) -> Dict[str, Any]:
        logger.info("[DOJO] Creating proving ground test script...")
        os.makedirs(str(DOJO_SANDBOX), exist_ok=True)
        
        test_id = str(uuid.uuid4())[:8]
        test_file_path = DOJO_SANDBOX / f"dream_stress_test_{test_id}.py"
        
        # Write exploit script to the proving ground
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(script_content)
            
        logger.info(f"[DOJO] Invoking TripletNexus verification harness on {test_file_path.name}...")
        try:
            # Execute validation check using the TripletNexus module with process group isolation
            nexus_path = WORKSPACE_ROOT / "Source" / "xoras_triplet_nexus.py"
            proc = subprocess.Popen(
                [sys.executable, str(nexus_path), str(test_file_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid
            )
            
            try:
                stdout, stderr = proc.communicate(timeout=15)
                returncode = proc.returncode
            except subprocess.TimeoutExpired:
                # Nuke the entire process group to prevent zombies
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                stdout, stderr = proc.communicate()
                return {
                    "blocked": True,
                    "reason": "Execution timed out (Chronos termination - PGID Killed)",
                    "stdout": stdout,
                    "stderr": "Timeout"
                }

            return {
                "blocked": "SUCCESS" in stdout or "Blocked" in stderr or returncode != 0,
                "returncode": returncode,
                "stdout": stdout,
                "stderr": stderr
            }
        except Exception as e:
            logger.error(f"[DOJO] Proving ground runtime error: {e}")
            return {"blocked": False, "error": str(e), "stdout": "", "stderr": ""}
        finally:
            try:
                if test_file_path.exists():
                    test_file_path.unlink()
            except Exception as e:
                logger.error(f"[DOJO] Cleanup error for {test_file_path.name}: {e}")

class MemoryConsolidation:
    """Consolidates dream insights and vulnerabilities into the hippocampus database and the semantic core."""
    @staticmethod
    async def log_dream_insight(archetype: str, narrative: str, test_result: Dict[str, Any]):
        ts = datetime.now(timezone.utc).isoformat()
        
        # 1. Write to local text registry
        log_entry = (
            f"=== DREAM INSIGHT ({ts}) ===\n"
            f"Archetype: {archetype}\n"
            f"Narrative: {narrative}\n"
            f"Sandbox Blocked: {test_result.get('blocked')}\n"
            f"Vulnerability Discovered: {not test_result.get('blocked')}\n"
            f"==================================================\n\n"
        )
        with open(DREAM_EXPERIMENT_LOG, "a", encoding="utf-8") as f:
            f.write(log_entry)
            
        # 2. Write to SQLite Database (HIPPOCAMPUS)
        try:
            os.makedirs(str(DREAM_DB.parent), exist_ok=True)
            with sqlite3.connect(DREAM_DB) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS dreams (
                        id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        seed TEXT,
                        mode TEXT,
                        content TEXT,
                        insights TEXT,
                        new_tools TEXT,
                        hypotheses TEXT,
                        artifacts TEXT,
                        questions TEXT,
                        duration_seconds REAL
                    )
                """)
                
                dream_id = hashlib.md5(f"{ts}_{archetype}".encode()).hexdigest()
                conn.execute(
                    "INSERT INTO dreams (id, timestamp, mode, content, insights, duration_seconds) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        dream_id, 
                        ts, 
                        archetype, 
                        narrative, 
                        json.dumps({"blocked": test_result.get("blocked"), "vulnerable": not test_result.get("blocked")}),
                        0.0
                    )
                )
                conn.commit()
            logger.info(f"[CONSOLIDATION] Synaptic data saved to: {DREAM_DB}")
        except Exception as e:
            logger.error(f"[CONSOLIDATION] Database insert failed: {e}")

        # 3. Funnel to Semantic Memory Core (ChromaDB)
        try:
            from xoras_persona_memory_bridge import get_memory_bridge
            bridge = get_memory_bridge()
            
            insight_text = (
                f"Narrative: {narrative} | "
                f"Vulnerability Hypothesis: Sandbox stress test run completed. "
                f"Blocked: {test_result.get('blocked')}. "
                f"Vulnerable: {not test_result.get('blocked')}."
            )
            await bridge.index_dream_insight(
                insight_text,
                archetype=archetype,
                persona_affinity="technical" if archetype == "danger" else "eccentric"
            )
            logger.info("[CONSOLIDATION] Dream insight funneled to Semantic Memory Core.")
        except Exception as e:
            logger.error(f"[CONSOLIDATION] Vector DB funneling failed: {e}")

class DreamOrchestrator:
    """Continuous background daemon managing the fuzzer-based dream loop (Hive Optimized)."""
    def __init__(self, cycle_interval_sec: float = 300.0):
        self.cycle_interval_sec = cycle_interval_sec
        self.running = False
        self.synthesis = ActivationSynthesisEngine()
        self.consecutive_failures = 0

    def verify_model_availability(self) -> bool:
        """Verifies that the target Ollama endpoint and model are ready. Returns False if fatal."""
        try:
            import requests
            res = requests.get("http://192.168.1.133:11434/api/tags", timeout=10)
            if res.status_code == 200:
                models = [m["name"] for m in res.json().get("models", [])]
                if MODEL_AFFINITY in models:
                    logger.info(f"[PREFLIGHT] Model '{MODEL_AFFINITY}' verified.")
                    return True
                else:
                    logger.error(f"[PREFLIGHT] Configured model '{MODEL_AFFINITY}' is missing. Active: {models}")
            else:
                logger.error(f"[PREFLIGHT] Ollama endpoint returned status {res.status_code}")
        except Exception as e:
            logger.error(f"[PREFLIGHT] Ollama service unreachable: {e}")
        return False

    async def run_cycle(self):
        logger.info("[DAEMON] Initiating dream loop cycle...")
        
        # 1. Harvest system noise
        entropy = EntropyHarvester.get_entropy_vector()
        logger.info(f"[DAEMON] Entropy signature: {entropy.get('source_hash', 'N/A')}")
        
        # 2. Synthesize dream narrative (threaded to prevent event loop starvation)
        loop = asyncio.get_running_loop()
        dream = await loop.run_in_executor(None, self.synthesis.generate_adversarial_hypothesis, entropy)
        
        # Check if we hit the fallback loop (which means synthesis failed)
        is_fallback = (
            dream.get("archetype") == "consolidation" and 
            dream.get("narrative") == "System entropy fallback dream cycle."
        )
        
        if is_fallback:
            self.consecutive_failures += 1
            logger.warning(f"[DAEMON] Synthesis fallback triggered. Consecutive failure count: {self.consecutive_failures}/3")
            if self.consecutive_failures >= 3:
                # Document critical incident to Error Catalyst
                try:
                    conn = sqlite3.connect(str(DOJO_SANDBOX / "Error_Catalyst" / "global_catalyst.db"))
                    conn.execute(
                        "INSERT INTO error_logs (timestamp, exception_type, error_message, status, healing_action) VALUES (?, ?, ?, ?, ?)",
                        (
                            datetime.now(timezone.utc).isoformat(),
                            "COGNITIVE_DECOUPLING",
                            "Model synthesis failed 3 times consecutively. Halting daemon execution loop.",
                            "OPEN",
                            "HALT_EXECUTION"
                        )
                    )
                    conn.commit()
                    conn.close()
                except Exception as db_err:
                    logger.error(f"[DAEMON] Failed to log incident: {db_err}")
                
                # Speak critical alert
                alert_msg = "Fatal: cognitive fuzzer decoupled due to consecutive LLM query failures. Stopping loop."
                subprocess.run([str(WORKSPACE_ROOT / "Source" / "xoras_say.sh"), alert_msg], capture_output=True)
                raise RuntimeError(alert_msg)
        else:
            self.consecutive_failures = 0

        logger.info(f"[DAEMON] Synthesized Archetype: {dream.get('archetype')}")
        logger.info(f"[DAEMON] Narrative Hypothesis: {dream.get('hypothesis')}")
        
        # 3. Deploy proving ground (threaded to run verification parallel to the daemon thread)
        script_code = dream.get("exploit_script", "")
        if script_code:
            test_res = await loop.run_in_executor(None, DojoProvingGround.run_stress_test, script_code)
            logger.info(f"[DAEMON] Proving ground run completed. Blocked status: {test_res.get('blocked')}")
            
            # 4. Consolidate memory (asynchronous DB logging and vector DB funneling)
            await MemoryConsolidation.log_dream_insight(
                dream.get("archetype", "consolidation"),
                dream.get("narrative", "unstructured reflection"),
                test_res
            )
        else:
            logger.warning("[DAEMON] Empty exploit script synthesized. Skipping stress test.")

    async def run_forever(self):
        # Preflight Check
        if not self.verify_model_availability():
            alert_msg = f"Fatal pre-flight check: local Ollama model {MODEL_AFFINITY} not ready. Aborting startup."
            subprocess.run([str(WORKSPACE_ROOT / "Source" / "xoras_say.sh"), alert_msg], capture_output=True)
            raise RuntimeError(alert_msg)

        self.running = True
        logger.info("[DAEMON] Dream daemon initialized.")
        while self.running:
            try:
                await self.run_cycle()
            except Exception as e:
                logger.error(f"[DAEMON] Exception in run loop: {e}")
                if "cognitive fuzzer decoupled" in str(e) or "Fatal pre-flight check" in str(e):
                    self.stop()
                    break
            logger.info(f"[DAEMON] Sleeping for {self.cycle_interval_sec} seconds...")
            await asyncio.sleep(self.cycle_interval_sec)

    def stop(self):
        self.running = False

if __name__ == "__main__":
    interval = float(os.environ.get("XORAS_DREAM_INTERVAL", "180.0"))
    orchestrator = DreamOrchestrator(cycle_interval_sec=interval)
    
    # Run a single demonstration cycle if launched directly
    if "--short" in sys.argv or os.environ.get("XORAS_SHORT_DREAM") == "true":
        asyncio.run(orchestrator.run_cycle())
    else:
        try:
            asyncio.run(orchestrator.run_forever())
        except KeyboardInterrupt:
            orchestrator.stop()
            logger.info("[DAEMON] Stopped by user command.")
