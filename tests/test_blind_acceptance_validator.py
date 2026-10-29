"""
Test Blind Acceptance on Independent Validator
===============================================
Requirement:
Submit a deliberately broken artifact; the validator must reject it without being told it's a test.
"""

import sys
import json
sys.path.append("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
from core.governance.independent_validator import IndependentBlackboxValidator

def run_blind_acceptance_test():
    validator = IndependentBlackboxValidator()

    # Broken Artifact 1: Syntax Error
    broken_syntax = "def broken_func():\n    return 100 +"
    passed, reason, meta = validator.validate_python_code(broken_syntax, required_functions=["broken_func"])
    print(f"[TEST 1: Syntax Defect] Passed={passed}, Reason={reason}")
    assert not passed, "Validator failed to catch syntax defect!"
    assert "AST_SYNTAX_ERROR" in reason

    # Broken Artifact 2: Missing Required Function
    missing_spec = "def other_func():\n    return 42\nif __name__ == '__main__':\n    pass"
    passed, reason, meta = validator.validate_python_code(missing_spec, required_functions=["required_operation"])
    print(f"[TEST 2: Schema Defect] Passed={passed}, Reason={reason}")
    assert not passed, "Validator failed to catch missing spec!"
    assert "SCHEMA_VIOLATION" in reason

    # Broken Artifact 3: Runtime Crash / Non-zero Exit Code
    crashing_code = "def compute():\n    raise RuntimeError('Simulated unhandled exception')\nif __name__ == '__main__':\n    compute()"
    passed, reason, meta = validator.validate_python_code(crashing_code, required_functions=["compute"])
    print(f"[TEST 3: Runtime Crash] Passed={passed}, Reason={reason}")
    assert not passed, "Validator failed to catch runtime crash!"
    assert "EXECUTION_FAILURE" in reason
    assert meta["exit_code"] != 0

    # Valid Artifact: Valid AST, Valid Signature, Clean Exit Code 0
    valid_code = "def compute():\n    return 42\nif __name__ == '__main__':\n    assert compute() == 42\n    print('Execution successful')"
    passed, reason, meta = validator.validate_python_code(valid_code, required_functions=["compute"])
    print(f"[TEST 4: Valid Artifact] Passed={passed}, Reason={reason}")
    assert passed, f"Validator falsely rejected valid artifact: {reason}"
    assert meta["exit_code"] == 0

    receipt = {
        "test_suite": "Independent Blind Validation Acceptance",
        "tests_executed": 4,
        "syntax_defect_caught": True,
        "schema_defect_caught": True,
        "runtime_crash_caught": True,
        "valid_code_passed": True,
        "verdict": "BLIND_VALIDATION_CERTIFIED"
    }

    receipt_file = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/catch_log/INDEPENDENT_VALIDATOR_RECEIPT.json"
    with open(receipt_file, "w") as f:
        json.dump(receipt, f, indent=2)

    print(f"\n[RECEIPT GENERATED] -> {receipt_file}")
    print(json.dumps(receipt, indent=2))

if __name__ == "__main__":
    run_blind_acceptance_test()
