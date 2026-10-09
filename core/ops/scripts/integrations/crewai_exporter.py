#!/usr/bin/env python3
"""
CrewAI to Chronos Swarm Debugger Exporter
-----------------------------------------------------------------------------
Captures CrewAI task execution steps, agent thoughts, and tool calls
and formats them into Chronos time-scrubbing .jsonl transcript files.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any

class ChronosCrewAIExporter:
    def __init__(self, log_path: str = "chronos_crewai_run.jsonl"):
        self.log_path = log_path
        self.step_index = 0

    def record_task_step(self, agent_role: str, task_description: str, task_output: str, internal_thoughts: str = ""):
        """Records a CrewAI task execution step."""
        entry = {
            "step_index": self.step_index,
            "source": "MODEL",
            "type": "CREWAI_TASK_STEP",
            "role": f"CrewAI::{agent_role}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "content": {
                "task": task_description,
                "result": task_output
            },
            "thinking": internal_thoughts
        }
        
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
        self.step_index += 1
        return entry

if __name__ == "__main__":
    exporter = ChronosCrewAIExporter("sample_crewai_chronos.jsonl")
    exporter.record_task_step(
        agent_role="Senior Research Analyst",
        task_description="Analyze competitive landscape for AI Observability",
        task_output="Identified 3 primary cloud SaaS competitors. High demand for offline zero-dependency debuggers.",
        internal_thoughts="Scraped 15 market reports. Users are complaining about $50k/year LangSmith bills."
    )
    print("Exported sample CrewAI run to sample_crewai_chronos.jsonl")
