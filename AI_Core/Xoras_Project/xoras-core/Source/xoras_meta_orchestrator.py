import os
import sys
import time
import json
import uuid
import asyncio
from typing import List, Dict, Any

# Ensure we can import modules from Source directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xoras_vector_db import query_semantic_memory, ingest_document, initialize_db
from xoras_dynamic_compiler import XorasDynamicCompiler
from xoras_swarm_governor import SwarmGovernor, AgentPriority

class XorasMetaOrchestrator:
    def __init__(self, use_grok: bool = False, use_governor: bool = True) -> None:
        self.use_grok = use_grok
        self.use_governor = use_governor
        initialize_db()
        
        # Initialize the Dynamic Compiler
        self.compiler = XorasDynamicCompiler()
        
        # Initialize Swarm Governor if requested
        self.governor = None
        if self.use_governor:
            self.governor = SwarmGovernor(
                spawn_fn=self._gov_spawn,
                hibernate_fn=self._gov_hibernate,
                rehydrate_fn=self._gov_rehydrate
            )
            # Run governor loop in background
            self.governor_task = asyncio.create_task(self.governor.run())

    def _gov_spawn(self, agent_id: str, priority: AgentPriority) -> None:
        """Governor callback to spawn/initialize an agent."""
        # The orchestrator handles instantiation dynamically; governor registration follows
        pass

    def _gov_hibernate(self, agent_id: str) -> Dict[str, Any]:
        """Governor callback to capture agent state snapshot."""
        # Simple snapshot of agent metadata
        return {"agent_id": agent_id, "hibernated_at": time.time()}

    def _gov_rehydrate(self, agent_id: str, state: Dict[str, Any]) -> None:
        """Governor callback to rehydrate agent from state snapshot."""
        pass

    def generate_dynamic_agent_code(self, class_name: str) -> str:
        """Generates dynamic class definition code for compile-time injection."""
        return f"""
class {class_name}:
    def __init__(self, name: str, role: str, instruction: str) -> None:
        self.name = name
        self.role = role
        self.instruction = instruction

    async def execute(self, shared_workspace: str, task_context: str) -> dict:
        import asyncio
        import xoras_vector_db

        # 1. Query semantic memory workspace
        search_query = f"{{self.role}} {{task_context}}"
        results = xoras_vector_db.query_semantic_memory(search_query, limit=3)

        # 2. Perform mock reasoning latency
        await asyncio.sleep(0.05)

        # 3. Formulate analysis report
        analysis_text = (
            f"Dynamic compiled analysis for {{self.role}} ({{self.name}}).\\n"
            f"Core Mandate: {{self.instruction}}\\n"
        )
        if "Designer" in self.role:
            analysis_text += "- Level layout structured procedural graph.\\n- Economy model balanced."
        elif "Analyst" in self.role:
            analysis_text += "- Cohort retention tracking initialized.\\n- Churn risk flag set."
        elif "Marketing" in self.role:
            analysis_text += "- Outreach channels verified.\\n- Ad spend target optimized."
        else:
            analysis_text += f"- General analysis on {{task_context}} finalized."

        return {{
            "agent": self.name,
            "role": self.role,
            "output": analysis_text
        }}
"""

    async def execute_swarm(self, task_description: str, shared_workspace: str = "meta_swarm_workspace") -> str:
        """Deconstructs task, dynamically compiles agents, executes them, and synthesizes reports."""
        print(f"[ORCHESTRATOR] Deconstructing task: {task_description}")
        sys.stdout.flush()

        # Define targets to spawn
        targets = []
        if "rogue-like" in task_description.lower() or "game" in task_description.lower():
            targets.append(("AresAgent", "Ares", "Game Designer", "Design core loop mechanics, progression trees, and level layouts.", AgentPriority.STANDARD))
            targets.append(("HestiaAgent", "Hestia", "Data Analyst", "Track retention metrics, player session lengths, and progression drops.", AgentPriority.STANDARD))
            targets.append(("HermesAgent", "Hermes", "Marketing Strategist", "Construct launch campaigns, trailers, and community outreach campaigns.", AgentPriority.EXPLORATORY))
        else:
            targets.append(("AlphaAgent", "Alpha", "Technical Lead", "Define the system design guidelines.", AgentPriority.CRITICAL))
            targets.append(("BetaAgent", "Beta", "QA Analyst", "Trace edge cases and write test parameters.", AgentPriority.STANDARD))

        outputs = []
        
        for class_name, name, role, instr, priority in targets:
            instance_id = f"{name.lower()}_{uuid.uuid4().hex[:6]}"
            
            # 1. Compile class dynamically
            code = self.generate_dynamic_agent_code(class_name)
            success, msg = await self.compiler.compile_class(class_name, code)
            if not success:
                print(f"[ORCHESTRATOR] AST/Compilation error for {class_name}: {msg}")
                sys.stdout.flush()
                continue
                
            # 2. Instantiate compiled class in sandbox
            success, msg = await self.compiler.instantiate_agent(class_name, instance_id, name, role, instr)
            if not success:
                print(f"[ORCHESTRATOR] Instantiation error for {instance_id}: {msg}")
                sys.stdout.flush()
                continue

            # 3. Register with Governor
            if self.governor:
                self.governor.register_agent(instance_id, priority)

            # 4. Execute and measure latency
            start_time = time.perf_counter()
            try:
                res = await self.compiler.execute_agent_method(instance_id, "execute", shared_workspace, task_description)
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                
                # Record latency in Governor
                if self.governor:
                    self.governor.record_latency(instance_id, elapsed_ms)
                
                outputs.append(res)
                
                # Write agent deliverable back to ChromaDB
                temp_filename = f"out_{name.lower()}_{uuid.uuid4().hex[:6]}.txt"
                temp_filepath = os.path.join("/tmp", temp_filename)
                
                file_content = (
                    f"Agent: {name}\n"
                    f"Role: {role}\n"
                    f"Analysis Deliverable:\n{res['output']}\n"
                    f"Workspace: {shared_workspace}"
                )
                
                with open(temp_filepath, "w", encoding="utf-8") as f:
                    f.write(file_content)
                    
                ingest_document(temp_filepath, domain=shared_workspace)
                try:
                    os.remove(temp_filepath)
                except OSError:
                    pass
                    
            except Exception as e:
                print(f"[ORCHESTRATOR] Execution failed for agent {instance_id}: {e}")
                sys.stdout.flush()

        # Synthesize outcomes into a Markdown report
        report_content = self._synthesize_report(task_description, outputs)

        # Write report to Docs/
        docs_dir = "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/Docs"
        os.makedirs(docs_dir, exist_ok=True)
        report_filename = f"meta_swarm_report_{uuid.uuid4().hex[:6]}.md"
        report_filepath = os.path.join(docs_dir, report_filename)

        with open(report_filepath, "w", encoding="utf-8") as f:
            f.write(report_content)

        print(f"[ORCHESTRATOR] Synthesized swarm report saved successfully to: {report_filepath}")
        sys.stdout.flush()

        return report_content

    def _synthesize_report(self, task: str, outputs: List[Dict[str, Any]]) -> str:
        report_lines = [
            f"# Swarm Synthesis Report: {task.title()}",
            f"\nGenerated by Xoras Meta-Agent Swarm Orchestrator on {time.asctime()}.",
            "\n## Shared Swarm Context Logs",
            "This report consolidates outputs from parallel dynamic agent nodes:\n"
        ]

        for out in outputs:
            report_lines.append(f"### Node: {out['agent']} | Role: {out['role']}")
            report_lines.append(f"{out['output']}")
            report_lines.append("\n" + "-"*40 + "\n")

        report_lines.append("## Unified Strategic Conclusions")
        report_lines.append("1. **Loop Integration:** Mechanics designed by Game Design map directly to retention indicators audited by Data Analysis.")
        report_lines.append("2. **Growth Loop:** The marketing launch plan leverages real-time community indicators seeded by the game logs.")

        return "\n".join(report_lines)

    def cleanup(self) -> None:
        """Cleans up background resources (governor loop and compiler worker)."""
        if self.governor:
            self.governor._running = False
            if hasattr(self, "governor_task"):
                self.governor_task.cancel()
        self.compiler.cleanup()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        task = sys.argv[1]
    else:
        task = "Design a space rogue-like game, analyze player retention, and outline a launch campaign."

    async def run_main():
        orchestrator = XorasMetaOrchestrator()
        try:
            await orchestrator.execute_swarm(task)
        finally:
            orchestrator.cleanup()

    asyncio.run(run_main())
