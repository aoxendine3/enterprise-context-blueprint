#!/usr/bin/env python3
"""
XORAS Agentic Framework — Basic Agent Example
Demonstrates environment initialization, tool execution, and signed trace receipts.
"""

from xoras import XORASAgentEnvironment

def main():
    print("=== XORAS Agent Framework — Basic Agent Example ===")
    env = XORASAgentEnvironment(config_path="xoras.env.yaml")

    # Execute a safe file write tool
    result = env.execute_tool(
        agent_name="Engineer",
        tool_name="file_write",
        args={
            "path": "artifacts/basic_agent_output.json",
            "content": '{"message": "Hello from XORAS Agent Framework v2.0", "status": "active"}'
        }
    )

    print("\nExecution Result:")
    print("Success:", result.get("success"))
    print("Path:", result.get("path"))
    print("Receipt Signature:", result.get("receipt_signature"))

if __name__ == "__main__":
    main()
