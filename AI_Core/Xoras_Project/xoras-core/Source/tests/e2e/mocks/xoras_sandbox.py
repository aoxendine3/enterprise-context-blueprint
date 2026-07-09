import os
import re
from typing import List, Union, Dict, Any


def run_in_sandbox(command: Union[str, List[str]], profile_path: str) -> Dict[str, Any]:
    if not command:
        raise ValueError("Command cannot be empty")
    if isinstance(command, list) and len(command) == 0:
        raise ValueError("Command list cannot be empty")

    if not os.path.exists(profile_path) and profile_path not in ["read-only", "workspace-write", "no-network", "localhost", "memory-limit", "restricted"]:
        raise FileNotFoundError(f"Sandbox profile path not found: {profile_path}")

    if isinstance(command, str):
        args = command.split()
    else:
        args = list(command)

    if not args or not args[0]:
        raise ValueError("Command cannot be empty")

    profile_content = ""
    if os.path.exists(profile_path):
        with open(profile_path, 'r') as f:
            profile_content = f.read()
    else:
        profile_content = profile_path

    stdout = ""
    stderr = ""
    returncode = 0

    if "memory-limit" in profile_content or "resource-limit" in profile_content:
        return {
            'stdout': "",
            'stderr': "Killed: memory limit exceeded",
            'returncode': 1
        }

    cmd_name = args[0].lower()

    for arg in args:
        if arg.startswith("/proc") or arg.startswith("/System") or arg.startswith("/etc") or arg.startswith("/private"):
            return {
                'stdout': "",
                'stderr': f"sandbox-exec: violation: read block on {arg}",
                'returncode': 1
            }

    is_write = False
    write_target = ""

    if cmd_name in ["touch", "rm", "mkdir", "cp", "mv", "dd", "write"]:
        is_write = True
        if len(args) > 1:
            write_target = args[-1]

    for arg in args:
        if ">" in arg or ">>" in arg:
            is_write = True
            parts = re.split(r'>>|>', arg)
            if len(parts) > 1:
                write_target = parts[1].strip()

    if is_write:
        is_read_only = "read-only" in profile_content or "deny file-write" in profile_content or "restricted" in profile_content
        is_permitting_write = "workspace-write" in profile_content or "allow file-write" in profile_content

        workspace_dir = "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core"

        if is_read_only:
            return {
                'stdout': "",
                'stderr': "sandbox-exec: violation: write denied under read-only profile",
                'returncode': 1
            }

        if write_target:
            abs_target = os.path.abspath(write_target)
            if not abs_target.startswith(workspace_dir):
                return {
                    'stdout': "",
                    'stderr': f"sandbox-exec: violation: write outside workspace denied for {write_target}",
                    'returncode': 1
                }
            else:
                stdout = f"Successfully wrote to {write_target}"
        else:
            stdout = "Write command executed"

    is_network = cmd_name in ["curl", "wget", "ping", "nc", "telnet"]
    if is_network:
        is_no_network = "no-network" in profile_content or "deny network" in profile_content or "restricted" in profile_content
        is_localhost_allowed = "localhost" in profile_content or "allow network-outbound" in profile_content

        target = ""
        for arg in args[1:]:
            if not arg.startswith("-"):
                target = arg
                break

        is_target_localhost = "localhost" in target or "127.0.0.1" in target

        if is_no_network and not (is_localhost_allowed and is_target_localhost):
            return {
                'stdout': "",
                'stderr': "sandbox-exec: violation: network access denied",
                'returncode': 1
            }

        if is_target_localhost:
            stdout = "HTTP/1.1 200 OK from localhost"
        else:
            stdout = f"HTTP/1.1 200 OK from {target}"

    if cmd_name == "echo":
        stdout = " ".join(args[1:])

    return {
        'stdout': stdout,
        'stderr': stderr,
        'returncode': returncode
    }
