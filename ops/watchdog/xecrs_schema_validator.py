import sys
import re

def validate_xecrs_report(filepath):
    try:
        with open(filepath, "r") as f:
            content = f.read()
            
        errors = []
        
        # 1. Must contain an Evidence Graph or Register
        if not re.search(r'(?i)(evidence\s+graph|evidence\s+register)', content):
            errors.append("MISSING_EVIDENCE_GRAPH: The report must include a structured Evidence Graph or Register.")
            
        # 2. Must contain a Verification Matrix
        if not re.search(r'(?i)verification\s+matrix', content):
            errors.append("MISSING_VERIFICATION_MATRIX: The report must include a Verification Matrix.")
            
        # 3. Must contain a Claim Ledger
        if not re.search(r'(?i)claim\s+ledger', content):
            errors.append("MISSING_CLAIM_LEDGER: The report must explicitly list claims in a Claim Ledger.")
            
        # 4. Must contain cryptographic hashes (SHA-256)
        if not re.search(r'[a-fA-F0-9]{64}', content):
            errors.append("MISSING_CRYPTO_HASH: The report must include at least one valid 64-character SHA-256 hash.")
            
        # 5. Must not contain fake/resolved statuses without evidence
        if "FAKE_STATUS_RESOLVED" in content:
            errors.append("MALFORMED_STATUS: Detected hardcoded or unverified fake resolved status.")
            
        if errors:
            print(f"🔴 [FAIL] Schema Validator rejected {filepath}:")
            for err in errors:
                print(f"   -> {err}")
            return False
            
        print(f"🟢 [PASS] Schema Validator accepted {filepath}.")
        return True
        
    except Exception as e:
        print(f"🔴 [FAIL] Could not read file {filepath}: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 xecrs_schema_validator.py <report_path>")
        sys.exit(1)
        
    success = validate_xecrs_report(sys.argv[1])
    sys.exit(0 if success else 1)
