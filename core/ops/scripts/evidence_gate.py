#!/usr/bin/env python3
"""
XORAS EVIDENCE-GATED MERKLE DAG COMMIT HANDLER
Verifies artifacts before allowing DAG commits:
  - file_exists   : Verifies target path exists on disk.
  - file_hash     : Verifies target file exists and matches expected SHA-256 hash.
  - cmd_exit      : Executes command and verifies zero exit status code.
  - test_pass     : Executes test suite/command and verifies pass (exit status 0).

Rejects non-evidenced or failed evidence payloads with non-zero exit code.
Outputs standard 64-hex SHA-256 Merkle root digest on success.
"""

import sys
import os
import argparse
import json
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DAG_STORE_FILE = ROOT / "memory" / "catch_log" / "merkle_catch_dag.json"
ROOT_HASH_FILE = ROOT / "memory" / "catch_log" / "merkle_root.hash"
GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def load_dag() -> list:
    if DAG_STORE_FILE.exists():
        try:
            data = json.loads(DAG_STORE_FILE.read_text(encoding='utf-8'))
            if isinstance(data, list):
                return data
        except Exception:
            pass
    return []

def save_dag(nodes: list) -> str:
    DAG_STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
    DAG_STORE_FILE.write_text(json.dumps(nodes, indent=2, ensure_ascii=False), encoding='utf-8')
    current_root = calculate_merkle_root(nodes)
    ROOT_HASH_FILE.write_text(current_root, encoding='utf-8')
    return current_root

def calculate_merkle_root(nodes: list) -> str:
    if not nodes:
        return GENESIS_HASH
    hashes = [n["node_hash"] for n in nodes]
    while len(hashes) > 1:
        if len(hashes) % 2 != 0:
            hashes.append(hashes[-1])
        hashes = [sha256_text(hashes[i] + hashes[i+1]) for i in range(0, len(hashes), 2)]
    return hashes[0]

def verify_evidence(evidence_type: str, target: str, expected_hash: str = "") -> tuple[bool, str, str]:
    """
    Returns (success: bool, artifact_hash: str, error_msg: str)
    """
    if not evidence_type or not target:
        return False, "", "Missing evidence_type or target"

    evidence_type = evidence_type.lower()
    
    if evidence_type == "file_exists":
        target_path = Path(target)
        if not target_path.exists():
            return False, "", f"File or path does not exist: '{target}'"
        artifact_hash = sha256_file(target_path) if target_path.is_file() else sha256_text(str(target_path))
        return True, artifact_hash, ""

    elif evidence_type == "file_hash":
        target_path = Path(target)
        if not target_path.is_file():
            return False, "", f"Target for file_hash is not a valid file: '{target}'"
        actual_hash = sha256_file(target_path)
        if expected_hash:
            if actual_hash.lower() != expected_hash.lower():
                return False, actual_hash, f"Hash mismatch for '{target}': expected '{expected_hash}', got '{actual_hash}'"
        return True, actual_hash, ""

    elif evidence_type in ("cmd_exit", "test_pass"):
        try:
            res = subprocess.run(target, shell=True, capture_output=True, text=True, timeout=30)
            if res.returncode != 0:
                err_snippet = (res.stderr or res.stdout or "").strip()[:200]
                return False, "", f"Command '{target}' failed with exit code {res.returncode}. Output: {err_snippet}"
            evidence_summary = f"{target}|exit:{res.returncode}|out:{res.stdout.strip()[:100]}"
            artifact_hash = sha256_text(evidence_summary)
            return True, artifact_hash, ""
        except subprocess.TimeoutExpired:
            return False, "", f"Command '{target}' timed out after 30 seconds"
        except Exception as e:
            return False, "", f"Execution error for '{target}': {str(e)}"

    else:
        return False, "", f"Unsupported evidence_type '{evidence_type}'. Supported: file_exists, file_hash, cmd_exit, test_pass"

def commit_evidenced_payload(agent: str, beat_type: str, payload: str, evidence_type: str, target: str, expected_hash: str = "") -> dict:
    if not payload or not payload.strip():
        raise ValueError("Payload cannot be empty")

    valid, artifact_hash, err_msg = verify_evidence(evidence_type, target, expected_hash)
    if not valid:
        raise ValueError(f"EVIDENCE VERIFICATION FAILED: {err_msg}")

    nodes = load_dag()
    index = len(nodes)
    parent_hash = nodes[-1]["node_hash"] if index > 0 else GENESIS_HASH
    ts = now_iso()
    
    raw_block = f"{index}|{ts}|{parent_hash}|{agent.lower()}|{beat_type.upper()}|{payload}|{evidence_type}|{artifact_hash}"
    node_hash = sha256_text(raw_block)

    node = {
        "index": index,
        "timestamp": ts,
        "node_hash": node_hash,
        "parent_hash": parent_hash,
        "agent_id": agent.lower(),
        "beat_type": beat_type.upper(),
        "payload": payload,
        "evidence_type": evidence_type.lower(),
        "artifact_hash": artifact_hash,
        "evidence_target": target
    }

    nodes.append(node)
    merkle_root = save_dag(nodes)
    return {
        "node": node,
        "merkle_root": merkle_root
    }

def main():
    parser = argparse.ArgumentParser(description="XORAS Evidence-Gated Merkle DAG Commit Handler")
    parser.add_argument("--agent", default="maxx", help="Agent persona committing payload")
    parser.add_argument("--beat-type", default="STATUS", help="Type of beat (STATUS, BUILD, AUDIT, TEST, etc.)")
    parser.add_argument("--payload", help="Payload content string")
    parser.add_argument("--evidence-type", choices=["file_exists", "file_hash", "cmd_exit", "test_pass"], help="Evidence verification type")
    parser.add_argument("--target", help="Evidence target (file path or command string)")
    parser.add_argument("--expected-hash", default="", help="Expected SHA-256 hash for file_hash check")
    parser.add_argument("--json", help="JSON payload containing commit parameters")

    args, positional = parser.parse_known_args()

    agent = args.agent
    beat_type = args.beat_type
    payload = args.payload
    evidence_type = args.evidence_type
    target = args.target
    expected_hash = args.expected_hash

    if args.json:
        try:
            jdata = json.loads(args.json)
            agent = jdata.get("agent", agent)
            beat_type = jdata.get("beat_type", beat_type)
            payload = jdata.get("payload", payload)
            evidence_type = jdata.get("evidence_type", evidence_type)
            target = jdata.get("target", target)
            expected_hash = jdata.get("expected_hash", expected_hash)
        except Exception as e:
            print(f"🚨 [EVIDENCE GATE REJECTED] Invalid JSON input: {e}", file=sys.stderr)
            sys.exit(1)

    if not payload and len(positional) >= 3:
        agent = positional[0]
        beat_type = positional[1]
        payload = positional[2]
        if len(positional) >= 4:
            evidence_type = positional[3]
        if len(positional) >= 5:
            target = positional[4]
        if len(positional) >= 6:
            expected_hash = positional[5]

    if not payload or not evidence_type or not target:
        print("🚨 [EVIDENCE GATE REJECTED] Missing required parameters. Payload, evidence-type, and target must be provided.", file=sys.stderr)
        print("Usage: python3 evidence_gate.py --agent <agent> --beat-type <type> --payload <payload> --evidence-type <file_exists|file_hash|cmd_exit|test_pass> --target <path|cmd>", file=sys.stderr)
        sys.exit(1)

    try:
        res = commit_evidenced_payload(agent, beat_type, payload, evidence_type, target, expected_hash)
        node = res["node"]
        root_digest = res["merkle_root"]
        print("=================================================================")
        print("🟢 [EVIDENCE GATE VERIFIED & COMMITTED]")
        print(f"Agent           : {node['agent_id']}")
        print(f"Beat Type       : {node['beat_type']}")
        print(f"Evidence Type   : {node['evidence_type']}")
        print(f"Artifact Hash   : {node['artifact_hash']}")
        print(f"Node Index      : {node['index']}")
        print(f"Node Hash       : {node['node_hash']}")
        print(f"SHA-256 Root    : {root_digest}")
        print("=================================================================")
        sys.exit(0)
    except Exception as e:
        print(f"🚨 [EVIDENCE GATE REJECTED] {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
