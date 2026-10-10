"""
XORAS Systems LLC — Configuration Schema Parser & Validator
Loads and validates xoras.env.yaml runtime configurations.
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass
class RuntimeConfig:
    environment_type: str = "agentic-sandbox"
    concurrency_limit: int = 8
    default_timeout_seconds: int = 120
    memory_limit_mb: int = 4096

@dataclass
class SecurityConfig:
    ast_verification: bool = True
    allow_network_egress: bool = True
    allowed_domains: List[str] = field(default_factory=lambda: ["github.com", "pypi.org"])
    secret_scanner: str = "env-integrity-sentry"
    block_deprecated_branding: bool = True

@dataclass
class AgentSpec:
    name: str
    role: str
    capabilities: List[str]

@dataclass
class AgentSwarmConfig:
    orchestrator_model: str = "gemini-2.5-flash"
    temperature: float = 0.1
    max_tokens: int = 8192
    agents: List[AgentSpec] = field(default_factory=list)

@dataclass
class XORASConfig:
    version: str
    organization: str
    runtime: RuntimeConfig
    security: SecurityConfig
    swarm: AgentSwarmConfig
    workspace_root: str
    log_output: str
    artifact_store: str

    @classmethod
    def load_from_yaml(cls, filepath: str = "xoras.env.yaml") -> "XORASConfig":
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"XORAS environment configuration not found at '{filepath}'")

        with open(filepath, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        rt_data = raw.get("runtime", {})
        runtime_cfg = RuntimeConfig(
            environment_type=rt_data.get("environment_type", "agentic-sandbox"),
            concurrency_limit=rt_data.get("concurrency_limit", 8),
            default_timeout_seconds=rt_data.get("default_timeout_seconds", 120),
            memory_limit_mb=rt_data.get("memory_limit_mb", 4096)
        )

        sec_data = raw.get("security", {})
        security_cfg = SecurityConfig(
            ast_verification=sec_data.get("ast_verification", True),
            allow_network_egress=sec_data.get("allow_network_egress", True),
            allowed_domains=sec_data.get("allowed_domains", ["github.com", "pypi.org"]),
            secret_scanner=sec_data.get("secret_scanner", "env-integrity-sentry"),
            block_deprecated_branding=sec_data.get("block_deprecated_branding", True)
        )

        swarm_raw = raw.get("agent_swarm", {})
        orch_raw = swarm_raw.get("orchestrator", {})
        agent_specs = []
        for a in swarm_raw.get("agents", []):
            agent_specs.append(AgentSpec(
                name=a.get("name", "Agent"),
                role=a.get("role", "Worker"),
                capabilities=a.get("capabilities", [])
            ))

        swarm_cfg = AgentSwarmConfig(
            orchestrator_model=orch_raw.get("model", "gemini-2.5-flash"),
            temperature=orch_raw.get("temperature", 0.1),
            max_tokens=orch_raw.get("max_tokens", 8192),
            agents=agent_specs
        )

        paths = raw.get("paths", {})
        return cls(
            version=raw.get("version", "2.0.0"),
            organization=raw.get("organization", "XORAS Systems LLC"),
            runtime=runtime_cfg,
            security=security_cfg,
            swarm=swarm_cfg,
            workspace_root=paths.get("workspace_root", "."),
            log_output=paths.get("log_output", "./logs/xoras_agent_traces.jsonl"),
            artifact_store=paths.get("artifact_store", "./artifacts")
        )
