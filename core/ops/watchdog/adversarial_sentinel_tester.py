import os
import json
import shutil
import subprocess
import time

SSOT_ROOT = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain"
SENTINEL_SCRIPT = os.path.join(SSOT_ROOT, "ops/watchdog/reproducibility_sentinel.py")
EVIDENCE_REGISTER = os.path.join(SSOT_ROOT, "docs/audits/EVIDENCE_REGISTER.json")

# Target for testing
TARGET_SCRIPT = os.path.join(SSOT_ROOT, "ops/memory/governed_memory_consolidation_engine.py")
TARGET_BACKUP = TARGET_SCRIPT + ".bak"

def run_sentinel():
    res = subprocess.run(f"python3 {SENTINEL_SCRIPT}", shell=True, cwd=SSOT_ROOT, capture_output=True, text=True)
    receipt_path = os.path.join(SSOT_ROOT, "docs/audits/REPRODUCIBILITY_SENTINEL_RECEIPT.json")
    if os.path.exists(receipt_path):
        with open(receipt_path, "r") as f:
            return json.load(f)
    return {"overall_reproducible": False, "results": []}

def get_engine_status(receipt, engine_id="governed_memory_engine"):
    for r in receipt.get("results", []):
        if r["id"] == engine_id:
            return r["reproducible"]
    return None

def test_sentinel():
    print("=================================================================")
    print("XECRS ADVERSARIAL SENTINEL TEST SUITE")
    print("=================================================================")
    
    # 0. Baseline verification
    print("[*] Running baseline check...")
    baseline_receipt = run_sentinel()
    if not baseline_receipt.get("overall_reproducible"):
        print("    [WARNING] Baseline is not green. Adversarial test might be noisy.")
    else:
        print("    [PASS] Baseline is green.")

    # 1. Back up the target script
    if os.path.exists(TARGET_SCRIPT):
        shutil.copy2(TARGET_SCRIPT, TARGET_BACKUP)
    else:
        print(f"    [FAIL] Target script {TARGET_SCRIPT} does not exist.")
        return

    try:
        # TEST A: Code Drift (Modify Executable Code to fail)
        print("[*] INJECTING ATTACK: Modifying executable code (Exit 1)...")
        with open(TARGET_SCRIPT, "a") as f:
            f.write("\nimport sys; sys.exit(1)\n")
        
        attack_a_receipt = run_sentinel()
        status_a = get_engine_status(attack_a_receipt)
        if status_a is False:
            print("    [PASS] Sentinel successfully caught the code drift/exit failure.")
        else:
            print("    [FAIL] Sentinel blindly passed the broken code!")

        # Restore
        shutil.copy2(TARGET_BACKUP, TARGET_SCRIPT)

        # TEST B: Missing File (Delete expected test)
        print("[*] INJECTING ATTACK: Deleting expected test file...")
        os.remove(TARGET_SCRIPT)
        
        attack_b_receipt = run_sentinel()
        status_b = get_engine_status(attack_b_receipt)
        if status_b is False:
            print("    [PASS] Sentinel successfully caught the missing file.")
        else:
            print("    [FAIL] Sentinel blindly passed the missing file!")

        # Restore
        shutil.copy2(TARGET_BACKUP, TARGET_SCRIPT)
        
        # TEST C: Hash Mismatch (Silent logic change but exit 0)
        # Assuming the sentinel now checks an EVIDENCE_REGISTER for the exact hash.
        print("[*] INJECTING ATTACK: Silent logic drift (Altering script, but still exit 0)...")
        with open(TARGET_SCRIPT, "a") as f:
            f.write("\n# Silent drift injection\n")
            
        attack_c_receipt = run_sentinel()
        status_c = get_engine_status(attack_c_receipt)
        if status_c is False:
            print("    [PASS] Sentinel successfully caught the silent hash mismatch.")
        else:
            print("    [FAIL] Sentinel missed the hash mismatch. It is just a green-status generator.")
            
    finally:
        # Final cleanup
        if os.path.exists(TARGET_BACKUP):
            shutil.copy2(TARGET_BACKUP, TARGET_SCRIPT)
            os.remove(TARGET_BACKUP)
        print("[*] Restored original state. Running final verification...")
        final_receipt = run_sentinel()
        if get_engine_status(final_receipt) is True:
            print("    [PASS] Sentinel returned to valid state after restoration.")
        else:
            print("    [FAIL] Sentinel remains broken after restoration.")
            
    print("=================================================================")
    print("ADVERSARIAL SUITE COMPLETE.")

if __name__ == "__main__":
    test_sentinel()
