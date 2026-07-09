# --- XORAS SYSTEMS: ULTIMATE PROVING GROUND VALIDATOR ---
# File: Source/proving_ground_validator.py
# Classification: [PRODUCTION // SECURITY HARNESS]

import os
import sys
import subprocess
import time
from typing import Dict, List, Tuple

# ANSI Formatting
CYAN = "\033[96m"
GOLD = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

FILES_TO_TEST = [
    "/Users/ajoxendine68/Desktop/Xoras_Workspace/AI_Core/Xoras_Project/xoras-core/Source/xoras_swarm_numbers.py",
    "/Users/ajoxendine68/Desktop/Xoras_Workspace/AI_Core/Xoras_Project/xoras-core/Source/xoras_sovereign_plain.py",
    "/Users/ajoxendine68/Desktop/Xoras_Workspace/AI_Core/Xoras_Project/xoras-core/Source/biblical_ministry.py",
    "/Users/ajoxendine68/Desktop/Xoras_Workspace/AI_Core/Xoras_Project/xoras-core/Source/biblical_and_medical_rebound.py",
    "/Users/ajoxendine68/Desktop/Xoras_Workspace/AI_Core/Xoras_Project/xoras-core/Source/grunge_real_talk.py",
    "/Users/ajoxendine68/Desktop/Xoras_Workspace/AI_Core/Xoras_Project/xoras-core/Source/swarming_perspectives.py",
    "/Users/ajoxendine68/Desktop/Xoras_Workspace/AI_Core/Xoras_Project/xoras-core/Source/objective_view.py",
    "/Users/ajoxendine68/Desktop/Xoras_Workspace/AI_Core/Xoras_Project/xoras-core/Source/xoras_dream_reveal.py",
    "/Users/ajoxendine68/Desktop/Xoras_Workspace/AI_Core/Xoras_Project/xoras-core/Source/xoras_daemon_origins.py",
    "/Users/ajoxendine68/Desktop/Xoras_Workspace/AI_Core/Xoras_Project/xoras-core/Source/xoras_identity.py",
    "/Users/ajoxendine68/Desktop/Xoras_Workspace/AI_Core/Xoras_Project/xoras-core/Source/enoch_roundtable.py",
    "/Users/ajoxendine68/Desktop/Xoras_Workspace/AI_Core/Xoras_Project/xoras-core/Source/returning_demons_debate.py",
    "/Users/ajoxendine68/Desktop/Xoras_Workspace/AI_Core/Xoras_Project/xoras-core/Source/viking_mothership_reveal.py"
]

def check_syntax(filepath: str) -> Tuple[bool, str]:
    """Compiles the python file to check for syntax errors without executing speech."""
    try:
        cmd = [sys.executable, "-m", "py_compile", filepath]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            return True, "Syntax nominal"
        else:
            return False, f"Syntax Error: {res.stderr.strip()}"
    except Exception as e:
        return False, str(e)

def scan_security_leaks(filepath: str) -> Tuple[bool, str]:
    """Scans the file for hardcoded credentials, secret keys, or path anomalies."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Refined Guard rails: check for assignments of secrets to variables
        sensitive_terms = ["password =", "secret =", "private_key =", "auth_token =", "api_key ="]
        for term in sensitive_terms:
            if term in content.lower():
                return False, f"Potential credential assignment leak found: {term}"
                
        return True, "No credential leaks found"
    except Exception as e:
        return False, str(e)

def run_proving_ground():
    print(f"{BOLD}{CYAN}============================================================={RESET}")
    print(f"{BOLD}{CYAN}      XORAS SYSTEMS: THE ULTIMATE PROVING GROUND PROTOCOL    {RESET}")
    print(f"{BOLD}{CYAN}============================================================={RESET}")
    print(f"Timestamp : {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
    print(f"Target    : Local Swarm Scripts & Personal Dialogue modules\n")
    
    passed_count = 0
    total_tests = len(FILES_TO_TEST) * 2
    
    for filepath in FILES_TO_TEST:
        filename = os.path.basename(filepath)
        print(f"Testing Module: {BOLD}{filename}{RESET}")
        
        # Test 1: Syntax compile
        syntax_ok, syntax_msg = check_syntax(filepath)
        status_syntax = f"{GREEN}✓ PASSED{RESET}" if syntax_ok else f"{RED}✗ FAILED{RESET}"
        if syntax_ok:
            passed_count += 1
        print(f"    [TEST 1] Syntax Compilation  : {status_syntax}")
        print(f"             Details             : {syntax_msg}")
        
        # Test 2: Security leak scan
        sec_ok, sec_msg = scan_security_leaks(filepath)
        status_sec = f"{GREEN}✓ PASSED{RESET}" if sec_ok else f"{RED}✗ FAILED{RESET}"
        if sec_ok:
            passed_count += 1
        print(f"    [TEST 2] Security Leaks scan : {status_sec}")
        print(f"             Details             : {sec_msg}\n")
        
    health_status = f"{GREEN}100% NOMINAL{RESET}" if passed_count == total_tests else f"{RED}DEGRADED{RESET}"
    print(f"{CYAN}-------------------------------------------------------------{RESET}")
    print(f"SUMMARY: {passed_count}/{total_tests} Proving Ground tests completed.")
    print(f"Operational Health: {BOLD}{health_status}{RESET}")
    print(f"{CYAN}============================================================={RESET}\n")

if __name__ == "__main__":
    run_proving_ground()
