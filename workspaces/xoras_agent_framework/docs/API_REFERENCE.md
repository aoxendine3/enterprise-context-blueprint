# XORAS Agentic Framework — API Reference

## Class: `XORASAgentEnvironment`
Located in `xoras.runtime`.

### Methods
- `__init__(config_path: str = "xoras.env.yaml")`: Boots agent runtime environment.
- `verify_ast_integrity(code_snippet: str) -> ASTScanResult`: Performs AST static analysis.
- `execute_tool(agent_name: str, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]`: Executes sandboxed tool.
- `log_trace(agent_name: str, action: str, payload: Dict[str, Any], status: str) -> EvidenceReceipt`: Signs and records execution trace.

---

## Class: `ASTSecurityEngine`
Located in `xoras.ast_security`.

### Methods
- `scan_code(code_snippet: str) -> ASTScanResult`: Scans code for forbidden AST nodes and entropy secret leaks.

---

## Class: `SwarmOrchestrator`
Located in `xoras.orchestrator`.

### Methods
- `run_pipeline(task_description: str, code_payload: str, target_path: str) -> Dict[str, Any]`: Runs multi-agent plan and execution pipeline across Architect, Engineer, and Auditor roles.
