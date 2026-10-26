"""
Unit tests for XORAS Agentic Runtime & Orchestrator.
"""

import os
from xoras.runtime import XORASAgentEnvironment
from xoras.orchestrator import SwarmOrchestrator

def test_runtime_file_write_and_read():
    env = XORASAgentEnvironment(config_path="xoras.env.yaml")
    write_res = env.execute_tool("Engineer", "file_write", {
        "path": "artifacts/test_artifact.json",
        "content": '{"version": "2.0.0", "status": "active"}'
    })
    assert write_res["success"] is True
    assert "receipt_signature" in write_res

    read_res = env.execute_tool("Engineer", "file_read", {
        "path": "artifacts/test_artifact.json"
    })
    assert read_res["success"] is True
    assert "active" in read_res["content"]

def test_runtime_ast_rejection():
    env = XORASAgentEnvironment(config_path="xoras.env.yaml")
    unsafe_res = env.execute_tool("Engineer", "file_write", {
        "path": "artifacts/bad.py",
        "content": 'eval("print(\'unsafe\')")'
    })
    assert unsafe_res["success"] is False
    assert "blocked by XORAS AST security" in unsafe_res["error"]

def test_swarm_orchestrator_pipeline():
    orch = SwarmOrchestrator()
    res = orch.run_pipeline(
        task_description="Deploy secure configuration manifest",
        code_payload='{"config": "valid_json"}',
        target_path="artifacts/swarm_output.json"
    )
    assert res["success"] is True
    assert res["stage"] == "COMPLETED"
    assert res["safety_score"] == 1.0
