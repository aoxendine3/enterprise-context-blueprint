#!/usr/bin/env python3
"""
Adversarial Stress Test Suite for Xoras OpenSource Toolkit (xoras-opensource)
-----------------------------------------------------------------------------
Executes boundary condition testing, fault injection, and edge-case fuzzing against:
1. xoras_sentinel/sentinel.py
2. chronos_debugger/index.html (via headless JS / JSONL log generator)

Goal: Expose all failure modes, unhandled exceptions, and missing sanitization logic.
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

TOOLKIT_DIR = Path("/tmp/xoras-opensource")
SENTINEL_SCRIPT = TOOLKIT_DIR / "xoras_sentinel" / "sentinel.py"

def test_sentinel_edge_cases():
    print("================================================================================")
    print("STRESS TEST 1: XORAS SENTINEL (FAULT INJECTION & ADVERSARIAL FUZZING)")
    print("================================================================================")
    
    results = []

    # Case 1.1: Special characters & shell injection symbols in query
    cmd1 = [sys.executable, str(SENTINEL_SCRIPT), "--query", "multi-agent & $KEY; | echo 'hacked'", "--limit", "1", "--model", "llama3.2:3b"]
    print("\n[Case 1.1] Testing query with shell metacharacters...")
    res1 = subprocess.run(cmd1, capture_output=True, text=True)
    success1 = (res1.returncode == 0)
    results.append(("Special Character Query Handling", success1, res1.stdout + res1.stderr))
    print(f"  --> Status: {'PASS' if success1 else 'FAIL (Exit code: ' + str(res1.returncode) + ')'}")

    # Case 1.2: Invalid/Non-existent Ollama Model Name
    cmd2 = [sys.executable, str(SENTINEL_SCRIPT), "--query", "agent", "--limit", "1", "--model", "non_existent_model_999"]
    print("\n[Case 1.2] Testing non-existent Ollama model handling...")
    res2 = subprocess.run(cmd2, capture_output=True, text=True)
    # Sentinel should NOT crash with an unhandled exception trace; it should catch the error gracefully
    success2 = ("Error: Local model unreachable" in res2.stdout or "Analysis failed" in res2.stdout or res2.returncode == 0)
    results.append(("Invalid Model Graceful Fallback", success2, res2.stdout + res2.stderr))
    print(f"  --> Status: {'PASS' if success2 else 'FAIL (Unhandled Crash)'}")

    # Case 1.3: Unreachable Ollama Host Port
    cmd3 = [sys.executable, str(SENTINEL_SCRIPT), "--query", "agent", "--limit", "1", "--host", "http://127.0.0.1:59999", "--model", "llama3.2:3b"]
    print("\n[Case 1.3] Testing unreachable host port...")
    res3 = subprocess.run(cmd3, capture_output=True, text=True)
    success3 = ("Error: Local model unreachable" in res3.stdout or res3.returncode == 0)
    results.append(("Unreachable Host Port Handling", success3, res3.stdout + res3.stderr))
    print(f"  --> Status: {'PASS' if success3 else 'FAIL (Unhandled Crash)'}")

    # Case 1.4: Zero Results Query
    cmd4 = [sys.executable, str(SENTINEL_SCRIPT), "--query", "xyz_nonexistent_repo_query_qwertyuiop123456789", "--limit", "1", "--model", "llama3.2:3b"]
    print("\n[Case 1.4] Testing 0-results query handling...")
    res4 = subprocess.run(cmd4, capture_output=True, text=True)
    success4 = ("No intelligence gathered" in res4.stdout or res4.returncode == 0)
    results.append(("Zero Results Query Handling", success4, res4.stdout + res4.stderr))
    print(f"  --> Status: {'PASS' if success4 else 'FAIL (Unhandled Crash)'}")

    return results

def generate_chronos_fuzz_jsonl():
    print("\n================================================================================")
    print("STRESS TEST 2: CHRONOS DEBUGGER (LOG FORMAT & UNICODE FUZZING)")
    print("================================================================================")

    fuzz_log_path = TOOLKIT_DIR / "chronos_debugger" / "fuzz_adversarial_log.jsonl"
    
    entries = [
        # Normal entry
        {"step_index": 0, "source": "USER_EXPLICIT", "type": "USER_INPUT", "created_at": "2026-10-09T18:00:00Z", "content": "Execute system test."},
        # Missing step_index and created_at
        {"source": "MODEL", "type": "PLANNER_RESPONSE", "role": "Maxx", "content": "Analyzing context pipeline."},
        # Unicode, emojis, and special control characters
        {"step_index": 2, "source": "MODEL", "type": "PLANNER_RESPONSE", "role": "Clara 🩺", "content": "Evaluating clinical safety 🚀 \x00\x07\x1b[31mRed Alert\x1b[0m"},
        # Malformed HTML / Script injection attempt in content
        {"step_index": 3, "source": "MODEL", "type": "PLANNER_RESPONSE", "role": "<script>alert('XSS')</script>", "content": "<img src=x onerror=alert('Hacked')> Security probe."},
        # Giant 100KB single line payload
        {"step_index": 4, "source": "MODEL", "type": "PLANNER_RESPONSE", "role": "Vance", "content": "A" * 100000}
    ]

    with open(fuzz_log_path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")
        # Add a raw corrupted non-JSON line at the end
        f.write("CORRUPTED_NON_JSON_LINE_RAW_TEXT_ABC123\n")

    print(f"  --> Generated fuzz test log: {fuzz_log_path} ({fuzz_log_path.stat().st_size} bytes)")
    return fuzz_log_path

def main():
    print("Executing Xoras Toolkit Adversarial Stress Test Suite...")
    sentinel_results = test_sentinel_edge_cases()
    fuzz_log = generate_chronos_fuzz_jsonl()

    print("\n================================================================================")
    print("STRESS TEST AUDIT SUMMARY")
    print("================================================================================")
    all_passed = True
    for test_name, status, log in sentinel_results:
        flag = "✅ PASS" if status else "❌ FAIL"
        print(f"[{flag}] {test_name}")
        if not status:
            all_passed = False
            print(f"--- ERROR LOG ---\n{log}\n-----------------")

    print("\nAdversarial Fuzz Log created for Chronos Debugger browser testing.")

if __name__ == "__main__":
    main()
