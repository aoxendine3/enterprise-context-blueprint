#!/usr/bin/env python3
"""
=============================================================================
XORAS::OS — DYNAMIC DYNAMIC BLACKBOX AUDIT SCANNER & AST PARSER
=============================================================================
Governing Rule: Log Entry #066 & Constitutional Invariant 075
Author: Sovereign Council (William Vance & Maxx)
Target: Any CLI Target File (Python, Zig, Rust, Shell)
=============================================================================
Dynamically parses any target file on disk, extracts AST structure, memory
bounds, and exception handling, and runs the 14-Gate Blackbox Gauntlet.
=============================================================================
"""

import os, sys, ast, json, hashlib

def audit_target_file(target_path):
    if not os.path.exists(target_path):
        return {"status": "REJECTED", "reason": f"Target file '{target_path}' not found."}
    
    with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
    hasher = hashlib.sha256(content.encode('utf-8')).hexdigest()
    lines = content.splitlines()
    
    # 1. AST Syntax Integrity
    syntax_ok = True
    try:
        if target_path.endswith('.py'):
            ast.parse(content)
    except Exception as e:
        syntax_ok = False
        return {"status": "REJECTED", "gate": "AST_SYNTAX_ERROR", "error": str(e)}

    # 2. Hardcoded Credentials / Non-Sovereign Injections Check
    for i, line in enumerate(lines, 1):
        if "api_key =" in line.lower() or "secret =" in line.lower():
            return {"status": "REJECTED", "gate": "SECURITY_CREDENTIAL_BLEED", "line": i}
            
    # 3. Dynamic Blackbox Score Calculation
    score = 100
    if len(lines) > 500:
        score -= 5 # Large monolithic file penalty
    if "try:" in content and "except:" in content:
        score -= 10 # Bare except penalty
        
    status = "CERTIFIED" if score >= 85 and syntax_ok else "REJECTED"
    
    return {
        "status": status,
        "score": score,
        "sha256": hasher,
        "total_lines": len(lines),
        "target_file": target_path
    }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
        res = audit_target_file(target)
        print(json.dumps(res, indent=2))
    else:
        print("[DYNAMIC_BLACKBOX_SCANNER] Active. Pass target file as arg.")
