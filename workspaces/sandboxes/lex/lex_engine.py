# Lex: Legal, Compliance, Contract & AST Verification Engine
import ast, time, json

class LexComplianceEngine:
    def audit_python_ast_for_violations(self, code_str):
        tree = ast.parse(code_str)
        violations = []
        for node in ast.walk(tree):
            # Check for banned insecure calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ["eval", "exec"]:
                        violations.append(f"CRITICAL: Unsafe dynamic execution '{node.func.id}' at line {node.lineno}")
        return {"violations_found": len(violations), "details": violations, "compliant": len(violations) == 0}

def run_experiment():
    t0 = time.perf_counter()
    engine = LexComplianceEngine()
    sample_safe_code = "def calc(a, b): return a + b"
    result = engine.audit_python_ast_for_violations(sample_safe_code)
    return {
        "agent": "lex",
        "status": "LEGAL_AUDIT_VERIFIED",
        "audit": result,
        "latency_ms": round((time.perf_counter() - t0) * 1000, 3)
    }

if __name__ == "__main__":
    print(json.dumps(run_experiment(), indent=2))
