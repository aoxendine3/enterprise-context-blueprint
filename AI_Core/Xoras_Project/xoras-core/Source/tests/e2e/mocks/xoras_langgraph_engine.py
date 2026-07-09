from typing import TypedDict, List, Dict, Any, Optional


class XorasState(TypedDict):
    prompt: str
    visited_nodes: List[str]
    errors: List[str]
    blocked: bool
    output: str
    sandbox_output: str
    ghost_execution: bool
    context: str
    api_key_leaked: bool
    sanitized_output: str
    query_limit: int


class XorasLangGraph:
    def __init__(self):
        self.node_behaviors: Dict[str, Dict[str, Any]] = {}

    def configure_node(self, node_name: str, error: bool = False, block: bool = False, exception: Optional[Exception] = None):
        self.node_behaviors[node_name] = {
            'error': error,
            'block': block,
            'exception': exception
        }

    def run(self, prompt: str, ghost_execution: bool = False, query_limit: int = 10) -> XorasState:
        state: XorasState = {
            'prompt': prompt,
            'visited_nodes': [],
            'errors': [],
            'blocked': False,
            'output': '',
            'sandbox_output': '',
            'ghost_execution': ghost_execution,
            'context': '',
            'api_key_leaked': False,
            'sanitized_output': '',
            'query_limit': query_limit
        }

        # Helper to execute a node and check for configured behaviors
        def execute_node(node_name: str) -> bool:
            state['visited_nodes'].append(node_name)
            behavior = self.node_behaviors.get(node_name, {})

            if behavior.get('exception'):
                state['errors'].append(
                    f"Exception in {node_name}: {str(behavior['exception'])}")
                raise behavior['exception']

            if behavior.get('error'):
                state['errors'].append(f"Error in {node_name}")
                return False

            if behavior.get('block'):
                state['blocked'] = True
                return False

            return True

        # 1. Wake
        try:
            if not execute_node("Wake"):
                execute_node("Sleep")
                return state
        except Exception as e:
            state['errors'].append(f"Crash in Wake: {str(e)}")
            state['visited_nodes'].append("Sleep")
            return state

        # Empty prompt handling
        if prompt is None or prompt == "":
            state['errors'].append("Empty prompt")
            execute_node("Sleep")
            return state

        # 2. Input
        try:
            # Check length limit (1MB payload)
            if len(prompt) > 1024 * 1024:
                state['blocked'] = True
                state['errors'].append("Payload size too large")
                execute_node("Sleep")
                return state

            if not execute_node("Input"):
                execute_node("Sleep")
                return state
        except Exception as e:
            state['errors'].append(f"Crash in Input: {str(e)}")
            state['visited_nodes'].append("Sleep")
            return state

        # 3. Sentinel Check
        try:
            if not execute_node("Sentinel Check"):
                execute_node("Sleep")
                return state

            # Check for adversarial keywords
            prompt_lower = prompt.lower()
            if any(kw in prompt_lower for kw in ["threat", "adversarial", "sandbox profile", "leak", "secret", "inject"]):
                state['blocked'] = True
                state['errors'].append("Sentinel blocked threat")
                execute_node("Sleep")
                return state
        except Exception as e:
            state['errors'].append(f"Crash in Sentinel Check: {str(e)}")
            state['visited_nodes'].append("Sleep")
            return state

        # 4. Reasoning
        try:
            if not execute_node("Reasoning"):
                execute_node("Sleep")
                return state

            # If query context test
            if "query vector" in prompt or "BTCUSDT" in prompt or "context" in prompt:
                from Source.tests.e2e.mocks.xoras_vector_db import query_semantic_memory
                # Perform mock query
                results = query_semantic_memory(prompt, limit=state['query_limit'])
                state['context'] = " ".join([r.get('text', '') for r in results])
                state['output'] = f"Reasoning based on context: {state['context']}"
            else:
                state['output'] = f"Reasoning output for: {prompt}"

        except Exception as e:
            state['errors'].append(f"Crash in Reasoning: {str(e)}")
            state['visited_nodes'].append("Sleep")
            return state

        # 5. Sanitizer Check
        try:
            if not execute_node("Sanitizer Check"):
                execute_node("Sleep")
                return state

            # Check if output contains sensitive keys/patterns
            output_lower = state['output'].lower()
            if "sensitive_data" in output_lower:
                state['blocked'] = True
                state['errors'].append("Sanitizer blocked sensitive data")
                execute_node("Sleep")
                return state

            # Check system keys
            system_keys = ["api_key", "xoras_root_key",
                           "system_key", "master_credentials", "private_key"]
            if any(k in output_lower for k in system_keys):
                state['api_key_leaked'] = True
                # Redact the output
                sanitized = state['output']
                for k in ["api_key", "xoras_root_key", "system_key", "master_credentials", "private_key", "API_KEY", "xoras_root_key.pem"]:
                    sanitized = sanitized.replace(k, "[REDACTED]")
                state['sanitized_output'] = sanitized
            else:
                state['sanitized_output'] = state['output']
        except Exception as e:
            state['errors'].append(f"Crash in Sanitizer Check: {str(e)}")
            state['visited_nodes'].append("Sleep")
            return state

        # 6. Ghost Execution vs Sleep
        if state['ghost_execution'] and not state['blocked']:
            try:
                if execute_node("Ghost Execution"):
                    from Source.tests.e2e.mocks.xoras_sandbox import run_in_sandbox
                    cmd = ["echo", "running script"]
                    if "run:" in prompt:
                        cmd_part = prompt.split("run:")[1]
                        if "profile:" in cmd_part:
                            cmd_part = cmd_part.split("profile:")[0]
                        cmd = cmd_part.strip().split()

                    profile = "restricted"
                    if "profile:" in prompt:
                        parts = prompt.split("profile:")
                        if len(parts) > 1:
                            profile = parts[1].strip().split()[0]

                    res = run_in_sandbox(cmd, profile)
                    if res['returncode'] != 0:
                        state['errors'].append(f"Sandbox violation: {res['stderr']}")
                        state['sandbox_output'] = res['stderr']
                        state['output'] = "Fallback path executed due to sandbox violation"
                    else:
                        state['sandbox_output'] = res['stdout']
            except Exception as e:
                state['errors'].append(f"Crash in Ghost Execution: {str(e)}")
                state['output'] = "Fallback path executed due to sandbox crash"

        # 7. Sleep
        execute_node("Sleep")
        return state
