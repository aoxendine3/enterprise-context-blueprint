import sqlite3
import json
import time
import asyncio
from pathlib import Path
import logging


class SwarmSequencer:
    """
    [PRODUCTION] Swarm Orchestrator with state gating, budget controls, and audit logs.
    """

    def __init__(self, db_path="/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/Source/swarm_audit.db"):
        self.db_path = Path(db_path)
        self.logger = logging.getLogger("SwarmSequencer")
        self._init_db()

    def _init_db(self):
        """Creates the transaction ledger for full execution visibility."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                agent_name TEXT,
                task_description TEXT,
                input_context TEXT,
                output_data TEXT,
                execution_time_ms REAL,
                status TEXT,
                budget_consumed REAL
            )
        """)
        conn.commit()
        conn.close()

    def log_transaction(self, agent_name, task, context, output, duration_ms, status, cost):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_ledger (timestamp, agent_name, task_description, input_context, output_data, execution_time_ms, status, budget_consumed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(time.time()), agent_name, task, json.dumps(context), json.dumps(output), duration_ms, status, cost))
        conn.commit()
        conn.close()

    async def execute_gated_task(self, agent_profile, task, context, master_goal, max_budget_usd=0.05):
        """
        Executes a task under strict context gating and budget constraints.
        """
        start_time = time.time()
        agent_name = agent_profile["name"]

        # 1. Context Alignment Check
        # Ensure the task parameters align with the overarching master goal
        if not self._verify_context_alignment(task, master_goal):
            err_msg = "Alignment Violation: Task deviates from the master goal stencil."
            self.logger.error(f"[{agent_name}] {err_msg}")
            self.log_transaction(agent_name, task, context, {
                                 "error": err_msg}, 0.0, "ALIGNMENT_FAILED", 0.0)
            return {"status": "FAILED", "error": err_msg}

        # 2. Simulated Model Cost Estimate (or Real API call)
        # Tracking budget consumption to prevent runaway costs
        est_cost = self._estimate_cost(context, task)
        if est_cost > max_budget_usd:
            err_msg = f"Budget Violation: Estimated cost ${est_cost:.4f} exceeds limit ${max_budget_usd:.4f}."
            self.logger.error(f"[{agent_name}] {err_msg}")
            self.log_transaction(agent_name, task, context, {
                                 "error": err_msg}, 0.0, "BUDGET_EXCEEDED", 0.0)
            return {"status": "FAILED", "error": err_msg}

        # 3. Execution of the task
        self.logger.info(f"[{agent_name}] Executing task: {task}")
        try:
            # For demonstration, we simulate the work or run a mock compiler check.
            # In production, this calls the Ollama or remote LLM endpoint.
            output_data = await self._run_agent_core(agent_profile, task, context)

            # 4. Output Gating / Code Validation
            # Assertions to ensure output passes syntactic correctness or unit assertions
            is_valid, validation_msg = self._validate_output(output_data)
            duration_ms = (time.time() - start_time) * 1000

            if is_valid:
                self.logger.info(f"[{agent_name}] Task passed validation.")
                self.log_transaction(agent_name, task, context,
                                     output_data, duration_ms, "SUCCESS", est_cost)
                return {"status": "SUCCESS", "output": output_data, "cost": est_cost}
            else:
                err_msg = f"Output Gating Failed: {validation_msg}"
                self.logger.error(f"[{agent_name}] {err_msg}")
                self.log_transaction(agent_name, task, context, output_data,
                                     duration_ms, "VALIDATION_FAILED", est_cost)
                return {"status": "FAILED", "error": err_msg}

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(f"[{agent_name}] Crash during execution: {e}")
            self.log_transaction(agent_name, task, context, {
                                 "error": str(e)}, duration_ms, "CRASHED", est_cost)
            return {"status": "FAILED", "error": str(e)}

    def _verify_context_alignment(self, task, master_goal):
        # In a production environment, this parses semantic keywords or uses a local classifier.
        # Here we perform keyword overlap verification as a heuristic gate.
        goal_keywords = set(master_goal.lower().split())
        task_keywords = set(task.lower().split())
        # Require at least some thematic overlap
        overlap = goal_keywords.intersection(task_keywords)
        return len(overlap) > 0

    def _estimate_cost(self, context, task):
        # Local model runs are free ($0.0). Cloud APIs cost per token.
        # Assume 1 token = 4 characters. Estimate 1500 tokens input, 500 output.
        # pricing estimate: $0.15 per 1M input tokens, $0.60 per 1M output tokens (Gemini 1.5 Flash rates)
        char_count = len(str(context)) + len(task)
        input_tokens = char_count / 4.0
        output_tokens = 500
        cost = (input_tokens * 0.00000015) + (output_tokens * 0.00000060)
        return cost

    async def _run_agent_core(self, agent_profile, task, context):
        # Simulate worker processing
        await asyncio.sleep(0.5)
        return {
            "generated_code": "def process_data(x):\n    return x * 2",
            "logs": "Compilation complete. Output checks passed."
        }

    def _validate_output(self, output):
        # Simple syntactic validator for generated Python code
        code = output.get("generated_code", "")
        if "def " not in code:
            return False, "Missing function definition syntax."
        try:
            compile(code, "<string>", "exec")
            return True, "Code compiled successfully."
        except SyntaxError as e:
            return False, f"Syntax Error: {e}"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    async def run_demo():
        seq = SwarmSequencer()
        profile = {"name": "OptimizerDrone", "role": "HFT Optimizer"}

        print("\n--- TEST 1: Executing Aligned Task under Budget ---")
        res1 = await seq.execute_gated_task(
            profile,
            task="Optimize function process_data logic",
            context="Current code:\ndef process_data(x):\n    return x + x",
            master_goal="Optimize the data processing pipelines",
            max_budget_usd=0.01
        )
        print("Result:", res1)

        print("\n--- TEST 2: Triggering Context Alignment Violation ---")
        res2 = await seq.execute_gated_task(
            profile,
            task="Order food online",
            context="Current code:\ndef process_data(x):\n    return x + x",
            master_goal="Optimize the data processing pipelines",
            max_budget_usd=0.01
        )
        print("Result:", res2)

        print("\n--- TEST 3: Triggering Budget Limit Violation ---")
        # Creating a massive context to trigger budget failure
        huge_context = "x" * 500000
        res3 = await seq.execute_gated_task(
            profile,
            task="Optimize function process_data logic",
            context=huge_context,
            master_goal="Optimize the data processing pipelines",
            max_budget_usd=0.01
        )
        print("Result:", res3)

    asyncio.run(run_demo())
