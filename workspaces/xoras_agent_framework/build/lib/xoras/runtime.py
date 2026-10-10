"""
XORAS Systems LLC — Agentic Runtime Harness
Manages agent execution loops, AST security verification, tool orchestration, and cryptographic trace receipts.
"""

import json
import logging
import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

from .config import XORASConfig
from .ast_security import ASTSecurityEngine, ASTScanResult
from .signer import CryptographicSigner, EvidenceReceipt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [XORAS-RUNTIME] %(message)s"
)

class XORASAgentEnvironment:
    def __init__(self, config_path: str = "xoras.env.yaml"):
        self.config_path = config_path
        self.workspace_root = os.getcwd()
        
        if os.path.exists(config_path):
            self.config = XORASConfig.load_from_yaml(config_path)
        else:
            logging.warning("Config '%s' not found, using default configuration.", config_path)
            self.config = None

        self.trace_file = os.path.join(self.workspace_root, "logs", "xoras_agent_traces.jsonl")
        os.makedirs(os.path.dirname(self.trace_file), exist_ok=True)
        
        self.ast_engine = ASTSecurityEngine(strict_mode=True)
        self.signer = CryptographicSigner()
        
        logging.info("Initialized XORAS Agentic Environment at %s", self.workspace_root)

    def verify_ast_integrity(self, code_snippet: str) -> ASTScanResult:
        """Runs AST static analysis check to enforce security guardrails."""
        return self.ast_engine.scan_code(code_snippet)

    def log_trace(self, agent_name: str, action: str, payload: Dict[str, Any], status: str) -> EvidenceReceipt:
        """Records deterministic structured execution trace with Ed25519 signature."""
        receipt = self.signer.sign_receipt(
            agent_id=agent_name,
            action=action,
            payload=payload,
            status=status
        )
        entry = {
            "version": receipt.version,
            "timestamp": receipt.timestamp,
            "organization": receipt.organization,
            "agent": receipt.agent_id,
            "action": receipt.action,
            "payload": payload,
            "payload_hash": receipt.payload_hash,
            "status": receipt.status,
            "signature": receipt.signature
        }
        with open(self.trace_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return receipt

    def execute_tool(self, agent_name: str, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Executes authorized agent tools within isolated workspace boundaries."""
        logging.info("Agent [%s] invoking tool [%s]", agent_name, tool_name)
        
        if tool_name == "bash_exec":
            command = args.get("command", "")
            ast_res = self.verify_ast_integrity(command)
            if not ast_res.is_safe:
                receipt = self.log_trace(agent_name, tool_name, args, "REJECTED_BY_AST_SECURITY")
                return {
                    "success": False,
                    "error": f"Command blocked by XORAS AST security: {', '.join(ast_res.violations)}",
                    "violations": ast_res.violations,
                    "receipt_signature": receipt.signature
                }
            
            try:
                import shlex
                timeout = self.config.runtime.default_timeout_seconds if self.config else 60
                cmd_args = shlex.split(command) if isinstance(command, str) else command
                res = subprocess.run(
                    cmd_args,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=self.workspace_root
                )
                output = {"stdout": res.stdout, "stderr": res.stderr, "exit_code": res.returncode}
                status = "SUCCESS" if res.returncode == 0 else "FAILED"
                receipt = self.log_trace(agent_name, tool_name, args, status)
                output["receipt_signature"] = receipt.signature
                return output
            except Exception as e:
                receipt = self.log_trace(agent_name, tool_name, args, "ERROR")
                return {"success": False, "error": str(e), "receipt_signature": receipt.signature}

        elif tool_name == "file_write":
            filepath = os.path.join(self.workspace_root, args.get("path", ""))
            content = args.get("content", "")
            
            ast_res = self.verify_ast_integrity(content)
            if not ast_res.is_safe:
                receipt = self.log_trace(agent_name, tool_name, args, "REJECTED_BY_AST_SECURITY")
                return {
                    "success": False,
                    "error": f"File content blocked by XORAS AST security: {', '.join(ast_res.violations)}",
                    "violations": ast_res.violations,
                    "receipt_signature": receipt.signature
                }

            try:
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                receipt = self.log_trace(agent_name, tool_name, args, "SUCCESS")
                return {
                    "success": True,
                    "path": filepath,
                    "bytes_written": len(content),
                    "receipt_signature": receipt.signature
                }
            except Exception as e:
                receipt = self.log_trace(agent_name, tool_name, args, "ERROR")
                return {"success": False, "error": str(e), "receipt_signature": receipt.signature}

        elif tool_name == "file_read":
            filepath = os.path.join(self.workspace_root, args.get("path", ""))
            try:
                if not os.path.exists(filepath):
                    return {"success": False, "error": f"File not found: {filepath}"}
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                receipt = self.log_trace(agent_name, tool_name, args, "SUCCESS")
                return {"success": True, "content": content, "receipt_signature": receipt.signature}
            except Exception as e:
                receipt = self.log_trace(agent_name, tool_name, args, "ERROR")
                return {"success": False, "error": str(e), "receipt_signature": receipt.signature}

        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

if __name__ == "__main__":
    env = XORASAgentEnvironment()
    test_res = env.execute_tool(
        agent_name="Engineer",
        tool_name="file_write",
        args={"path": "artifacts/status.json", "content": '{"status": "XORAS Agent Environment Active"}'}
    )
    print("Environment Test Result:", test_res)
