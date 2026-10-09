#!/usr/bin/env python3
"""
LangGraph to Chronos Swarm Debugger Exporter
-----------------------------------------------------------------------------
Captures LangGraph execution state nodes, thoughts, and message history
and formats them into Chronos time-scrubbing .jsonl transcript files.
"""

import json
import time
from datetime import datetime, timezone
from typing import List, Dict, Any

class ChronosLangGraphExporter:
    def __init__(self, log_path: str = "chronos_langgraph_run.jsonl"):
        self.log_path = log_path
        self.step_index = 0

    def record_node_execution(self, node_name: str, input_state: Dict[str, Any], output_state: Dict[str, Any], reasoning: str = ""):
        """Records a LangGraph node state transition."""
        entry = {
            "step_index": self.step_index,
            "source": "MODEL",
            "type": "LANGGRAPH_NODE_STEP",
            "role": f"LangGraph::{node_name}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "content": {
                "input_state": input_state,
                "output_state": output_state
            },
            "thinking": reasoning
        }
        
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
        self.step_index += 1
        return entry

if __name__ == "__main__":
    exporter = ChronosLangGraphExporter("sample_langgraph_chronos.jsonl")
    exporter.record_node_execution(
        node_name="PlannerAgent",
        input_state={"query": "Synthesize Q3 market trend"},
        output_state={"plan": ["fetch_news", "summarize_sentiment"]},
        reasoning="Query requires multi-source web retrieval and sentiment extraction."
    )
    print("Exported sample LangGraph run to sample_langgraph_chronos.jsonl")
