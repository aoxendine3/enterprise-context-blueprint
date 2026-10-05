import os
import subprocess
import json

SSOT_ROOT = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain"
VALIDATOR = os.path.join(SSOT_ROOT, "ops/watchdog/xecrs_schema_validator.py")
TEST_FILE = os.path.join(SSOT_ROOT, "scratch/test_report.md")
RECEIPT_FILE = os.path.join(SSOT_ROOT, "docs/audits/VALIDATOR_GAUNTLET_RECEIPT.json")

KNOWN_GOOD_REPORT = """
# XECRS Test Report
## Claim Ledger
- Claim 1: The system works.
## Verification Matrix
| Component | Status |
| --- | --- |
| DB | Verified |
## Evidence Graph
[Claim] -> [Evidence]
## Receipts
Merkle Root: 5b76674d9f55cec30bc5cbf8f88d42bf6311e5adc22db38c4b640a7e0d57bf59
"""

def write_test(content):
    with open(TEST_FILE, "w") as f:
        f.write(content)

def run_validator():
    proc = subprocess.run(["python3", VALIDATOR, TEST_FILE], capture_output=True, text=True)
    return proc.returncode == 0, proc.stdout

def run_gauntlet():
    print("=================================================================")
    print("XECRS ADVERSARIAL MUTATION GAUNTLET (Who Validates the Validator?)")
    print("=================================================================")
    
    results = []

    # 1. Known Good
    write_test(KNOWN_GOOD_REPORT)
    passed, stdout = run_validator()
    res = {"mutation": "Known Good Baseline", "expected": "PASS", "actual": "PASS" if passed else "FAIL", "validator_output": stdout.strip()}
    results.append(res)
    print(f"[*] Test 1: {res['mutation']} -> {'✅ SUCCESS (Validator Allowed)' if passed else '❌ FAILED'}")

    # 2. Missing Claim Ledger
    bad_report = KNOWN_GOOD_REPORT.replace("Claim Ledger", "Random List")
    write_test(bad_report)
    passed, stdout = run_validator()
    res = {"mutation": "Missing Claim Ledger", "expected": "FAIL", "actual": "PASS" if passed else "FAIL", "validator_output": stdout.strip()}
    results.append(res)
    print(f"[*] Test 2: {res['mutation']} -> {'✅ SUCCESS (Validator Blocked)' if not passed else '❌ FAILED'}")

    # 3. Missing Verification Matrix
    bad_report = KNOWN_GOOD_REPORT.replace("Verification Matrix", "Simple Table")
    write_test(bad_report)
    passed, stdout = run_validator()
    res = {"mutation": "Missing Verification Matrix", "expected": "FAIL", "actual": "PASS" if passed else "FAIL", "validator_output": stdout.strip()}
    results.append(res)
    print(f"[*] Test 3: {res['mutation']} -> {'✅ SUCCESS (Validator Blocked)' if not passed else '❌ FAILED'}")

    # 4. Broken Hash
    bad_report = KNOWN_GOOD_REPORT.replace("5b76674d9f55cec30bc5cbf8f88d42bf6311e5adc22db38c4b640a7e0d57bf59", "5b76674d9f55cec30bc5cbf8f88d42bf6311e5adc22db38c") # truncated
    write_test(bad_report)
    passed, stdout = run_validator()
    res = {"mutation": "Truncated/Broken SHA-256 Hash", "expected": "FAIL", "actual": "PASS" if passed else "FAIL", "validator_output": stdout.strip()}
    results.append(res)
    print(f"[*] Test 4: {res['mutation']} -> {'✅ SUCCESS (Validator Blocked)' if not passed else '❌ FAILED'}")
    
    # 5. Fake Resolved Status
    bad_report = KNOWN_GOOD_REPORT + "\nStatus: FAKE_STATUS_RESOLVED"
    write_test(bad_report)
    passed, stdout = run_validator()
    res = {"mutation": "Fake Resolved Status Inserted", "expected": "FAIL", "actual": "PASS" if passed else "FAIL", "validator_output": stdout.strip()}
    results.append(res)
    print(f"[*] Test 5: {res['mutation']} -> {'✅ SUCCESS (Validator Blocked)' if not passed else '❌ FAILED'}")

    # Generate Receipt
    total_passed = sum(1 for r in results if r["expected"] == r["actual"])
    success_rate = (total_passed / len(results)) * 100
    
    receipt = {
        "gauntlet_name": "Who Validates the Validator",
        "total_mutations_tested": len(results),
        "validator_catch_rate": f"{success_rate}%",
        "details": results
    }
    
    with open(RECEIPT_FILE, "w") as f:
        json.dump(receipt, f, indent=2)

    print("-----------------------------------------------------------------")
    print(f"VALIDATOR CATCH RATE: {success_rate}%")
    print(f"[RECEIPT] Written to {RECEIPT_FILE}")
    print("=================================================================")

if __name__ == "__main__":
    run_gauntlet()
