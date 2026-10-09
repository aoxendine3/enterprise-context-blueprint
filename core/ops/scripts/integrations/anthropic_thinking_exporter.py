#!/usr/bin/env python3
"""
Anthropic Claude Thinking Block Exporter for Chronos Swarm Debugger
-----------------------------------------------------------------------------
Captures Claude 3.5 Sonnet extended thinking / reasoning blocks and formats them
into Chronos time-scrubbing .jsonl transcript files.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any

class ChronosClaudeThinkingExporter:
    def __init__(self, log_path: str = "chronos_claude_thinking.jsonl"):
        self.log_path = log_path
        self.step_index = 0

    def record_thinking_step(self, role: str, prompt: str, thinking_content: str, response_text: str):
        """Records an Anthropic extended thinking reasoning block."""
        entry = {
            "step_index": self.step_index,
            "source": "MODEL",
            "type": "CLAUDE_EXTENDED_THINKING",
            "role": f"Claude::{role}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "content": {
                "prompt": prompt,
                "response": response_text
            },
            "thinking": thinking_content
        }
        
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
        self.step_index += 1
        return entry

if __name__ == "__main__":
    exporter = ChronosClaudeThinkingExporter("sample_claude_thinking.jsonl")
    exporter.record_thinking_step(
        role="CodeArchitect",
        prompt="Design a zero-copy shared memory buffer in C for arm64",
        thinking_content="Need 128-byte cache line alignment. Will use POSIX shm_open and mmap with std::atomic flags.",
        response_text="Here is the zero-copy C implementation with 128-byte alignment..."
    )
    print("Exported sample Claude Thinking run to sample_claude_thinking.jsonl")
