import os
import ast
import re

CHURN_DIR = "/Users/ajoxendine68/Desktop/Projects/GitHub_Repos/aoxendine3_remote_pull/Customer-Churn-Prediction"
XORAS_DIR = "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core"

class CodeAuditor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.secrets = []
        self.issues = []

    def visit_Assign(self, node):
        # Look for hardcoded keys, secrets, tokens
        for target in node.targets:
            if isinstance(target, ast.Name):
                name = target.id.upper()
                if any(x in name for x in ["KEY", "SECRET", "PASSWORD", "TOKEN", "CREDENTIALS"]):
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        val = node.value.value
                        # Ignore obviously empty or mock values
                        if len(val) > 4 and val not in ["mock", "dummy", "test", "your_key", "secret_key"]:
                            self.secrets.append((node.lineno, target.id))
        self.generic_visit(node)

    def visit_Call(self, node):
        # Look for iterrows usage (known performance issue)
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "iterrows":
                self.issues.append((node.lineno, "Performance: iterrows() used. Use vectorised operations or .itertuples() instead."))
        self.generic_visit(node)

def audit_directory(directory):
    total_files = 0
    compiled_files = 0
    all_secrets = []
    all_issues = []
    
    for root, _, files in os.walk(directory):
        if "venv" in root or ".git" in root or "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                total_files += 1
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        code = f.read()
                    
                    # 1. AST compilation check
                    tree = ast.parse(code, filename=filepath)
                    compiled_files += 1
                    
                    # 2. Audit AST nodes
                    auditor = CodeAuditor(filepath)
                    auditor.visit(tree)
                    
                    # 3. Regex checks for MongoDB strings in code
                    if "mongodb+srv://" in code:
                        # Extract the line
                        for idx, line in enumerate(code.splitlines(), 1):
                            if "mongodb+srv://" in line and not any(x in line for x in ["example", "placeholder"]):
                                all_secrets.append((filepath, idx, "Potential MongoDB Connection String"))

                    for lineno, name in auditor.secrets:
                        all_secrets.append((filepath, lineno, f"Hardcoded secret assignment: {name}"))
                    for lineno, msg in auditor.issues:
                        all_issues.append((filepath, lineno, msg))
                        
                except SyntaxError as se:
                    all_issues.append((filepath, se.lineno, f"Syntax Error: {se.text.strip()} ({se.msg})"))
                except Exception as e:
                    all_issues.append((filepath, 0, f"Error processing file: {e}"))
                    
    return total_files, compiled_files, all_secrets, all_issues

def main():
    print("=== [AUDIT] Initiating Production-Grade Code Audit ===")
    
    print("\n--- Auditing ChurnShield Pro ---")
    c_tot, c_comp, c_sec, c_iss = audit_directory(CHURN_DIR)
    print(f"Total Python Files: {c_tot}")
    print(f"Successfully Compiled: {c_comp}")
    print(f"Issues Found: {len(c_iss)}")
    for f, l, msg in c_iss:
        print(f"  [ISSUE] {os.path.basename(f)}:L{l} - {msg}")
    print(f"Potential Secrets Found: {len(c_sec)}")
    for f, l, msg in c_sec:
        print(f"  [SECRET] {os.path.basename(f)}:L{l} - {msg}")

    print("\n--- Auditing Xoras Swarm Core ---")
    x_tot, x_comp, x_sec, x_iss = audit_directory(XORAS_DIR)
    print(f"Total Python Files: {x_tot}")
    print(f"Successfully Compiled: {x_comp}")
    print(f"Issues Found: {len(x_iss)}")
    for f, l, msg in x_iss:
        print(f"  [ISSUE] {os.path.basename(f)}:L{l} - {msg}")
    print(f"Potential Secrets Found: {len(x_sec)}")
    for f, l, msg in x_sec:
        print(f"  [SECRET] {os.path.basename(f)}:L{l} - {msg}")

if __name__ == "__main__":
    main()
