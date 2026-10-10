#!/usr/bin/env python3
"""
XORAS Agentic Framework — AST Code Security Evaluator
Demonstrates AST static analysis and rejection of unsafe dynamic code snippets.
"""

from xoras import ASTSecurityEngine

def evaluate_snippets():
    engine = ASTSecurityEngine()
    
    snippets = [
        ("Safe Data Handler", "def process(x):\n    return x.strip().lower()\n"),
        ("Dynamic Eval Snippet", "eval('import os; os.system(\"ls\")')\n"),
        ("Unsafe Subprocess", "import subprocess\nsubprocess.Popen('rm -rf /tmp', shell=True)\n"),
        ("Hardcoded API Key", "AWS_SECRET_ACCESS_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'\n")
    ]

    print("=== XORAS AST Security Evaluator Demo ===")
    for title, code in snippets:
        res = engine.scan_code(code)
        print(f"\n[Snippet]: {title}")
        print(f"Status: {'SAFE [PASSED]' if res.is_safe else 'UNSAFE [REJECTED]'}")
        print(f"Safety Score: {res.safety_score * 100:.1f}%")
        if res.violations:
            print("Violations:", res.violations)
        if res.secrets_detected:
            print("Secrets:", res.secrets_detected)

if __name__ == "__main__":
    evaluate_snippets()
