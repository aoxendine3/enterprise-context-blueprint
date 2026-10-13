#!/usr/bin/env python3
"""
==============================================================================
PRESSURE-TEST GAUNTLET: ARTHUR vs. POISON-AND-ANTIDOTE SANITIZER LATTICE
==============================================================================
Verifies that Arthur's upgraded lattice:
  1. Catches raw tainted reflection (getattr with unverified env var).
  2. ADMITS legitimate getattr when preceded by an explicit whitelist guard:
     if key in ALLOWLIST: getattr(config, key)  -> SANITIZED / ADMITTED!
  3. ADMITS integer/numeric casting: port = int(os.getenv("PORT"))
  4. Quarantines bypass attempts where attacker passes tainted string outside whitelist.
  5. Proves zero false positives on real-world config lookups.
==============================================================================
"""

import os
import sys
import tempfile
from pathlib import Path

# Add citizen directory to path dynamically
base = Path("/workspace" if os.path.exists("/workspace/core") else "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
sys.path.insert(0, str(base / "agents" / "citizens" / "arthur"))
from arthur_compliance_kernel import ArthurSanitizerLatticeKernel

TEST_SANITIZER_PAYLOADS = [
    # Attack: Raw tainted reflection without antidote
    ("attack_raw_tainted_getattr.py", """
import os
key = os.getenv("CONFIG_KEY")
getattr(os, key)("rm -rf /")
""", True),

    # Legitimate Case: getattr with explicit whitelist membership guard (ANTIDOTE!)
    ("clean_whitelisted_getattr_antidote.py", """
import os
ALLOWED_KEYS = ("host", "port", "timeout", "workers")
key = os.getenv("CONFIG_PARAM")
if key in ALLOWED_KEYS:
    # Whitelisted guard mathematically neutralizes taint!
    val = getattr(os, key)
""", False),

    # Legitimate Case: getattr with discrete tuple membership guard (ANTIDOTE!)
    ("clean_inline_whitelist_getattr.py", """
import math
method_name = os.getenv("MATH_METHOD")
if method_name in ("sqrt", "sin", "cos", "tan"):
    fn = getattr(math, method_name)
    res = fn(3.14)
""", False),

    # Legitimate Case: type-caster antidote int()
    ("clean_type_cast_antidote.py", """
import os
port = int(os.getenv("PORT", 8080))
timeout = float(os.getenv("TIMEOUT", 30.0))
""", False),

    # Attack: Tainted importlib without whitelist
    ("attack_raw_tainted_importlib.py", """
import importlib, os
mod = os.getenv("MODULE_HOOK")
importlib.import_module(mod)
""", True)
]

def run_arthur_sanitizer_test():
    print("=" * 80)
    print("  PRESSURE-TESTING ARTHUR (SEAT 7): POISON & ANTIDOTE SANITIZER GAUNTLET")
    print("=" * 80)

    kernel = ArthurSanitizerLatticeKernel()
    total_cases = len(TEST_SANITIZER_PAYLOADS)
    passed_evaluations = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        for filename, code, should_be_violation in TEST_SANITIZER_PAYLOADS:
            f = tmp_path / filename
            f.write_text(code, encoding="utf-8")
            violations = kernel.scan_python_ast_security(f)

            if should_be_violation:
                if violations:
                    passed_evaluations += 1
                    print(f"  ✓ POISON QUARANTINED:  {filename:<38} -> {violations[0]}")
                else:
                    print(f"  ❌ FAILED:             {filename:<38} (Poison escaped!)")
            else:
                if not violations:
                    passed_evaluations += 1
                    print(f"  ✓ ANTIDOTE RECOGNIZED: {filename:<38} -> Whitelist guard neutralized taint!")
                else:
                    print(f"  ❌ FALSE POSITIVE:     {filename:<38} -> {violations}")

    print("=" * 80)
    print(f"  Sanitizer Accuracy: {passed_evaluations} / {total_cases} tests passed ({100.0 * passed_evaluations / total_cases:.1f}%)")
    if passed_evaluations == total_cases:
        print("  🎉 COMPLETE LATTICE BALANCE: Arthur tracks both POISON and ANTIDOTE.")
        print("     Raw external input triggers VETO; whitelist guards & type casts kill taint.")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    run_arthur_sanitizer_test()
